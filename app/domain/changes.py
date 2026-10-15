"""Internal domain models for the four supported change kinds.

These are product abstractions — not AWS resource dictionaries, HCL, or
Terraform argument bags.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import (
    DesiredAction,
    DnsRecordType,
    IpProtocol,
    ListenerProtocol,
    RouteActionType,
    TrafficDirection,
)
from app.domain.errors import DomainValidationError
from app.domain.network import (
    validate_certificate_arn,
    validate_cidr,
    validate_dns_name,
    validate_dns_record_values,
    validate_listener_arn,
    validate_listener_port,
    validate_priority,
    validate_security_group_id,
    validate_sg_protocol_ports,
    validate_ttl,
)

_LB_NAME_RE = re.compile(r"^[A-Za-z0-9-]{1,32}$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class DnsRecordChange(_StrictModel):
    """Internal DNS record intent."""

    change_kind: Literal["dns_record"] = "dns_record"
    action: DesiredAction
    name: str
    record_type: DnsRecordType
    values: tuple[str, ...]
    ttl_seconds: int = 300
    hosted_zone_name: str | None = None

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        return validate_dns_name(value, field="name")

    @field_validator("hosted_zone_name")
    @classmethod
    def _zone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_dns_name(value, field="hosted_zone_name")

    @field_validator("ttl_seconds")
    @classmethod
    def _ttl(cls, value: int) -> int:
        return validate_ttl(value)

    @model_validator(mode="after")
    def _values(self) -> DnsRecordChange:
        normalized = validate_dns_record_values(self.record_type, list(self.values))
        object.__setattr__(self, "values", tuple(normalized))
        return self


class FixedResponseAction(_StrictModel):
    action_type: Literal[RouteActionType.FIXED_RESPONSE] = RouteActionType.FIXED_RESPONSE
    status_code: int = Field(ge=200, le=499)
    content_type: str = "text/plain"
    message_body: str = "ok"

    @field_validator("content_type")
    @classmethod
    def _content_type(cls, value: str) -> str:
        if not value or len(value) > 64:
            raise DomainValidationError(
                "content_type must be 1-64 characters",
                field="content_type",
            )
        return value

    @field_validator("message_body")
    @classmethod
    def _body(cls, value: str) -> str:
        if len(value) > 1024:
            raise DomainValidationError(
                "message_body must be at most 1024 characters",
                field="message_body",
            )
        return value


class ForwardAction(_StrictModel):
    action_type: Literal[RouteActionType.FORWARD] = RouteActionType.FORWARD
    target_group_arn: str

    @field_validator("target_group_arn")
    @classmethod
    def _tg(cls, value: str) -> str:
        if not value.startswith("arn:aws:elasticloadbalancing:"):
            raise DomainValidationError(
                "target_group_arn must be an ELB target group ARN",
                field="target_group_arn",
            )
        if ":targetgroup/" not in value:
            raise DomainValidationError(
                "target_group_arn must be an ELB target group ARN",
                field="target_group_arn",
            )
        return value


RouteAction = Annotated[
    FixedResponseAction | ForwardAction,
    Field(discriminator="action_type"),
]


class LoadBalancerRouteChange(_StrictModel):
    """Internal load balancer listener/route intent."""

    change_kind: Literal["load_balancer_route"] = "load_balancer_route"
    action: DesiredAction
    load_balancer_name: str = Field(min_length=1, max_length=32)
    listener_port: int
    listener_protocol: ListenerProtocol
    priority: int
    path_pattern: str | None = None
    host_header: str | None = None
    route_action: RouteAction

    @field_validator("load_balancer_name")
    @classmethod
    def _lb_name(cls, value: str) -> str:
        if not _LB_NAME_RE.fullmatch(value):
            raise DomainValidationError(
                "load_balancer_name must be 1-32 chars of [a-zA-Z0-9-]",
                field="load_balancer_name",
            )
        return value

    @field_validator("priority")
    @classmethod
    def _priority(cls, value: int) -> int:
        return validate_priority(value)

    @field_validator("path_pattern")
    @classmethod
    def _path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.startswith("/"):
            raise DomainValidationError(
                "path_pattern must start with '/'",
                field="path_pattern",
            )
        if len(value) > 128:
            raise DomainValidationError(
                "path_pattern must be at most 128 characters",
                field="path_pattern",
            )
        return value

    @field_validator("host_header")
    @classmethod
    def _host(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_dns_name(value, field="host_header")

    @model_validator(mode="after")
    def _consistency(self) -> LoadBalancerRouteChange:
        validate_listener_port(self.listener_port, self.listener_protocol)
        if self.path_pattern is None and self.host_header is None:
            raise DomainValidationError(
                "at least one of path_pattern or host_header is required",
                field="path_pattern",
            )
        if self.listener_protocol is ListenerProtocol.HTTPS and isinstance(
            self.route_action,
            FixedResponseAction,
        ):
            # HTTPS with fixed-response is allowed; TLS cert attachment is a
            # separate change type. No contradiction here.
            pass
        return self


class TlsBindingChange(_StrictModel):
    """Internal TLS certificate attachment / reference intent."""

    change_kind: Literal["tls_binding"] = "tls_binding"
    action: DesiredAction
    listener_arn: str
    certificate_arn: str
    default_certificate: bool = True

    @field_validator("listener_arn")
    @classmethod
    def _listener(cls, value: str) -> str:
        return validate_listener_arn(value)

    @field_validator("certificate_arn")
    @classmethod
    def _cert(cls, value: str) -> str:
        return validate_certificate_arn(value)


class SecurityGroupRuleChange(_StrictModel):
    """Internal security group rule intent."""

    change_kind: Literal["security_group_rule"] = "security_group_rule"
    action: DesiredAction
    security_group_id: str
    direction: TrafficDirection
    protocol: IpProtocol
    from_port: int | None = None
    to_port: int | None = None
    cidr_blocks: tuple[str, ...] = ()
    source_security_group_id: str | None = None
    description: str = Field(min_length=1, max_length=255)

    @field_validator("security_group_id")
    @classmethod
    def _sg(cls, value: str) -> str:
        return validate_security_group_id(value)

    @field_validator("source_security_group_id")
    @classmethod
    def _source_sg(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_security_group_id(value, field="source_security_group_id")

    @field_validator("cidr_blocks")
    @classmethod
    def _cidrs(cls, value: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        return tuple(validate_cidr(item, field="cidr_blocks") for item in value)

    @model_validator(mode="after")
    def _consistency(self) -> SecurityGroupRuleChange:
        from_port, to_port = validate_sg_protocol_ports(
            self.protocol,
            self.from_port,
            self.to_port,
        )
        object.__setattr__(self, "from_port", from_port)
        object.__setattr__(self, "to_port", to_port)

        has_cidr = bool(self.cidr_blocks)
        has_source = self.source_security_group_id is not None
        if has_cidr == has_source:
            raise DomainValidationError(
                "exactly one of cidr_blocks or source_security_group_id is required",
                field="cidr_blocks",
            )
        if has_cidr and len(self.cidr_blocks) > 10:
            raise DomainValidationError(
                "at most 10 cidr_blocks are allowed per request",
                field="cidr_blocks",
            )

        # Local contradiction checks — not live inventory overlap.
        if has_cidr:
            networks = [ipaddress.ip_network(c) for c in self.cidr_blocks]
            for i, left in enumerate(networks):
                for right in networks[i + 1 :]:
                    if left.overlaps(right):
                        raise DomainValidationError(
                            "cidr_blocks within a request must not overlap",
                            field="cidr_blocks",
                        )
            if any(str(c) == "0.0.0.0/0" for c in self.cidr_blocks):
                if self.direction is TrafficDirection.INGRESS and self.protocol in {
                    IpProtocol.TCP,
                    IpProtocol.UDP,
                    IpProtocol.ALL,
                }:
                    admin_ports = {22, 3389}
                    if self.protocol is IpProtocol.ALL or (
                        self.from_port is not None
                        and self.to_port is not None
                        and any(self.from_port <= p <= self.to_port for p in admin_ports)
                    ):
                        raise DomainValidationError(
                            "unrestricted administrative ingress to 0.0.0.0/0 is not allowed",
                            field="cidr_blocks",
                        )
        return self


DomainChange = Annotated[
    DnsRecordChange | LoadBalancerRouteChange | TlsBindingChange | SecurityGroupRuleChange,
    Field(discriminator="change_kind"),
]
