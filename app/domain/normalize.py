"""Normalize inbound API requests into typed domain change specifications."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from app.domain.change_request import ChangeRequest
from app.domain.change_spec import ChangeSpecification, deferred_checks_for
from app.domain.changes import (
    DnsRecordChange,
    DomainChange,
    FixedResponseAction,
    ForwardAction,
    LoadBalancerRouteChange,
    SecurityGroupRuleChange,
    TlsBindingChange,
)
from app.domain.enums import ChangeType, LifecycleEvent, LifecycleState, RouteActionType
from app.domain.errors import DomainValidationError
from app.domain.ids import ChangeSpecId, RequestId
from app.domain.inbound import (
    InboundChangeRequest,
    InboundDnsRecord,
    InboundFixedResponse,
    InboundForward,
    InboundLoadBalancerRoute,
    InboundSecurityGroupRule,
    InboundTlsBinding,
)
from app.domain.validation_errors import raise_as_domain_validation


def parse_inbound(data: dict[str, Any]) -> InboundChangeRequest:
    """Parse caller input into the API-facing inbound model."""
    try:
        return InboundChangeRequest.model_validate(data)
    except ValidationError as exc:
        raise_as_domain_validation(exc)
        raise  # pragma: no cover


def to_domain_change(inbound: InboundChangeRequest) -> DomainChange:
    """Map inbound payload to an internal domain change with semantic checks."""
    change = inbound.change
    try:
        if isinstance(change, InboundDnsRecord):
            return DnsRecordChange(
                action=change.action,
                name=change.name,
                record_type=change.record_type,
                values=tuple(change.values),
                ttl_seconds=change.ttl_seconds,
                hosted_zone_name=change.hosted_zone_name,
            )
        if isinstance(change, InboundLoadBalancerRoute):
            if isinstance(change.route_action, InboundFixedResponse):
                route_action: FixedResponseAction | ForwardAction = FixedResponseAction(
                    action_type=RouteActionType.FIXED_RESPONSE,
                    status_code=change.route_action.status_code,
                    content_type=change.route_action.content_type,
                    message_body=change.route_action.message_body,
                )
            elif isinstance(change.route_action, InboundForward):
                route_action = ForwardAction(
                    action_type=RouteActionType.FORWARD,
                    target_group_arn=change.route_action.target_group_arn,
                )
            else:  # pragma: no cover - discriminator exhaustiveness
                raise DomainValidationError("unsupported route_action", field="route_action")
            return LoadBalancerRouteChange(
                action=change.action,
                load_balancer_name=change.load_balancer_name,
                listener_port=change.listener_port,
                listener_protocol=change.listener_protocol,
                priority=change.priority,
                path_pattern=change.path_pattern,
                host_header=change.host_header,
                route_action=route_action,
            )
        if isinstance(change, InboundTlsBinding):
            return TlsBindingChange(
                action=change.action,
                listener_arn=change.listener_arn,
                certificate_arn=change.certificate_arn,
                default_certificate=change.default_certificate,
            )
        if isinstance(change, InboundSecurityGroupRule):
            return SecurityGroupRuleChange(
                action=change.action,
                security_group_id=change.security_group_id,
                direction=change.direction,
                protocol=change.protocol,
                from_port=change.from_port,
                to_port=change.to_port,
                cidr_blocks=tuple(change.cidr_blocks),
                source_security_group_id=change.source_security_group_id,
                description=change.description,
            )
    except ValidationError as exc:
        raise_as_domain_validation(exc)
        raise  # pragma: no cover
    except DomainValidationError:
        raise

    raise DomainValidationError("unsupported change type", field="change")


def change_type_of(change: DomainChange) -> ChangeType:
    return ChangeType(change.change_kind)


def build_change_specification(
    *,
    request_id: RequestId,
    environment: Any,
    change: DomainChange,
    created_at: datetime | None = None,
) -> ChangeSpecification:
    change_type = change_type_of(change)
    deferred = deferred_checks_for(change_type)
    # Identity is content-addressed over normalized intent (excludes request ids /
    # timestamps) so identical intents are comparable for future idempotency.
    identity_payload = {
        "schema_version": 1,
        "environment": environment.value if hasattr(environment, "value") else environment,
        "change_type": change_type.value,
        "change": change.model_dump(mode="json"),
        "deferred_checks": [item.value for item in deferred],
    }
    return ChangeSpecification(
        change_spec_id=ChangeSpecId.from_canonical_payload(identity_payload),
        request_id=request_id,
        environment=environment,
        change_type=change_type,
        change=change,
        created_at=created_at or datetime.now(UTC),
        deferred_checks=deferred,
    )


def accept_change_request(
    data: dict[str, Any],
    *,
    request_id: RequestId | None = None,
    now: datetime | None = None,
) -> tuple[ChangeRequest, ChangeSpecification]:
    """Validate + normalize an inbound request into request + change specification.

    Starts in REQUESTED, then transitions to VALIDATED on success or FAILED on
    domain validation failure (returned via exception — callers that want a
    FAILED record can catch and materialize separately).
    """
    stamp = now or datetime.now(UTC)
    rid = request_id or RequestId.generate()
    inbound = parse_inbound(data)

    request = ChangeRequest(
        request_id=rid,
        environment=inbound.environment,
        change_type=ChangeType(inbound.change.change_type),
        actor=inbound.actor,
        state=LifecycleState.REQUESTED,
        idempotency_key=inbound.idempotency_key,
        created_at=stamp,
        updated_at=stamp,
    )

    try:
        domain_change = to_domain_change(inbound)
        spec = build_change_specification(
            request_id=rid,
            environment=inbound.environment,
            change=domain_change,
            created_at=stamp,
        )
    except DomainValidationError:
        # Caller observes failure by exception; HTTP layer (M3) can persist FAILED.
        raise

    validated = request.apply(LifecycleEvent.VALIDATION_SUCCEEDED).with_change_spec_id(
        spec.change_spec_id
    )
    return validated, spec
