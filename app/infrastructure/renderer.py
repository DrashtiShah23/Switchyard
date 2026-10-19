"""Render ChangeSpecification into deterministic Terraform module inputs.

Consumes only normalized domain change specifications (plus explicit render
context for environment-bound identifiers). Never accepts raw HCL, Terraform
CLI args, or arbitrary AWS resource dictionaries from callers.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.change_spec import ChangeSpecification
from app.domain.changes import (
    DnsRecordChange,
    FixedResponseAction,
    ForwardAction,
    LoadBalancerRouteChange,
    SecurityGroupRuleChange,
    TlsBindingChange,
)
from app.domain.enums import DesiredAction, IpProtocol, TrafficDirection
from app.domain.errors import DomainValidationError


class RenderContext(BaseModel):
    """Environment-bound values that callers cannot invent as free-form infra."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hosted_zone_id: str | None = None
    # Keys: "{load_balancer_name}:{listener_port}" → listener ARN
    listener_arns: dict[str, str] = Field(default_factory=dict)


class TerraformModuleInput(BaseModel):
    """Typed module invocation request produced from a ChangeSpecification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    module_name: Literal["dns", "security_group", "listener_rule", "tls"]
    variables: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "variables": self.variables,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class UnsupportedChangeForRenderer(DomainValidationError):
    """Change type is valid in domain but not rendered by this renderer."""


class ChangeSpecificationRenderer:
    """Map ChangeSpecification → module inputs for all four change kinds."""

    def render(
        self,
        specification: ChangeSpecification,
        *,
        context: RenderContext | None = None,
    ) -> TerraformModuleInput:
        ctx = context or RenderContext()
        change = specification.change
        if isinstance(change, DnsRecordChange):
            return self._render_dns(change, context=ctx)
        if isinstance(change, SecurityGroupRuleChange):
            return self._render_security_group_rule(change)
        if isinstance(change, LoadBalancerRouteChange):
            return self._render_load_balancer_route(change, context=ctx)
        if isinstance(change, TlsBindingChange):
            return self._render_tls_binding(change)
        kind = getattr(change, "change_kind", type(change))
        raise UnsupportedChangeForRenderer(
            f"renderer does not support change_kind={kind!r}",
            field="change_kind",
        )

    def _render_dns(
        self,
        change: DnsRecordChange,
        *,
        context: RenderContext,
    ) -> TerraformModuleInput:
        if not context.hosted_zone_id:
            raise DomainValidationError(
                "hosted_zone_id is required in render context for DNS changes "
                "(environment-bound; zones are not created by this renderer)",
                field="hosted_zone_id",
            )
        if not context.hosted_zone_id.startswith("Z"):
            raise DomainValidationError(
                "hosted_zone_id must look like a Route 53 hosted zone id",
                field="hosted_zone_id",
            )

        variables: dict[str, Any] = {
            "zone_id": context.hosted_zone_id,
            "record_name": change.name,
            "record_type": change.record_type.value,
            "ttl_seconds": change.ttl_seconds,
            "records": list(change.values),
            "allow_overwrite": change.action is DesiredAction.UPDATE,
            "tags": {
                "Project": "switchyard",
                "Component": "dns",
                "ManagedBy": "terraform",
            },
        }
        if change.hosted_zone_name is not None:
            variables["tags"] = {
                **variables["tags"],
                "HostedZoneName": change.hosted_zone_name,
            }

        return TerraformModuleInput(module_name="dns", variables=variables)

    def _render_security_group_rule(
        self,
        change: SecurityGroupRuleChange,
    ) -> TerraformModuleInput:
        protocol = self._aws_protocol(change.protocol)
        rule: dict[str, Any] = {
            "description": change.description,
            "protocol": protocol,
        }
        if change.from_port is not None:
            rule["from_port"] = change.from_port
        if change.to_port is not None:
            rule["to_port"] = change.to_port
        if change.cidr_blocks:
            rules = [{**rule, "cidr_ipv4": cidr} for cidr in change.cidr_blocks]
        else:
            rules = [
                {
                    **rule,
                    "referenced_security_group_id": change.source_security_group_id,
                }
            ]

        variables: dict[str, Any] = {
            "create_security_group": False,
            "existing_security_group_id": change.security_group_id,
            "ingress_rules": rules if change.direction is TrafficDirection.INGRESS else [],
            "egress_rules": rules if change.direction is TrafficDirection.EGRESS else [],
            "tags": {
                "Project": "switchyard",
                "Component": "security_group",
                "ManagedBy": "terraform",
            },
        }
        return TerraformModuleInput(module_name="security_group", variables=variables)

    def _render_load_balancer_route(
        self,
        change: LoadBalancerRouteChange,
        *,
        context: RenderContext,
    ) -> TerraformModuleInput:
        key = f"{change.load_balancer_name}:{change.listener_port}"
        listener_arn = context.listener_arns.get(key)
        if not listener_arn:
            raise DomainValidationError(
                "listener_arns render context must include "
                f"{key!r} (environment-bound; no live AWS lookup)",
                field="listener_arns",
            )
        if not listener_arn.startswith("arn:aws:elasticloadbalancing:"):
            raise DomainValidationError(
                "listener_arns values must be ELB listener ARNs",
                field="listener_arns",
            )

        action = self._lb_action(change.route_action)
        variables: dict[str, Any] = {
            "listener_arn": listener_arn,
            "priority": change.priority,
            "path_pattern": change.path_pattern,
            "host_header": change.host_header,
            "action": action,
            "tags": {
                "Project": "switchyard",
                "Component": "listener_rule",
                "ManagedBy": "terraform",
                "LoadBalancerName": change.load_balancer_name,
                "ListenerProtocol": change.listener_protocol.value,
            },
        }
        return TerraformModuleInput(module_name="listener_rule", variables=variables)

    def _render_tls_binding(self, change: TlsBindingChange) -> TerraformModuleInput:
        # Certificate reference/attachment only — never ACM issuance.
        # is_default records intent; alb module owns listener default certificate_arn.
        variables: dict[str, Any] = {
            "listener_arn": change.listener_arn,
            "certificate_arn": change.certificate_arn,
            "is_default": change.default_certificate,
            "tags": {
                "Project": "switchyard",
                "Component": "tls",
                "ManagedBy": "terraform",
                "DesiredAction": change.action.value,
            },
        }
        return TerraformModuleInput(module_name="tls", variables=variables)

    @staticmethod
    def _lb_action(action: FixedResponseAction | ForwardAction) -> dict[str, Any]:
        if isinstance(action, FixedResponseAction):
            return {
                "type": "fixed-response",
                "status_code": str(action.status_code),
                "content_type": action.content_type,
                "message_body": action.message_body,
            }
        return {
            "type": "forward",
            "target_group_arn": action.target_group_arn,
        }

    @staticmethod
    def _aws_protocol(protocol: IpProtocol) -> str:
        if protocol is IpProtocol.ALL:
            return "-1"
        return protocol.value
