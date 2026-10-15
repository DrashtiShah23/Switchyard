"""API-facing request shapes (product contract), separate from internal models.

These models describe what a caller may submit. They deliberately exclude HCL,
Terraform arguments, AWS resource dictionaries, shell commands, and free-form
configuration blobs. Milestone 3 FastAPI routes will adapt HTTP to these types;
they are not FastAPI-specific themselves.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import (
    DesiredAction,
    DnsRecordType,
    Environment,
    IpProtocol,
    ListenerProtocol,
    RouteActionType,
    TrafficDirection,
)
from app.domain.errors import DomainValidationError
from app.domain.ids import IdempotencyKey


class _InboundModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class InboundDnsRecord(_InboundModel):
    change_type: Literal["dns_record"] = "dns_record"
    action: DesiredAction
    name: str
    record_type: DnsRecordType
    values: list[str]
    ttl_seconds: int = 300
    hosted_zone_name: str | None = None


class InboundFixedResponse(_InboundModel):
    action_type: Literal["fixed_response"] = RouteActionType.FIXED_RESPONSE.value
    status_code: int = 200
    content_type: str = "text/plain"
    message_body: str = "ok"


class InboundForward(_InboundModel):
    action_type: Literal["forward"] = RouteActionType.FORWARD.value
    target_group_arn: str


InboundRouteAction = Annotated[
    InboundFixedResponse | InboundForward,
    Field(discriminator="action_type"),
]


class InboundLoadBalancerRoute(_InboundModel):
    change_type: Literal["load_balancer_route"] = "load_balancer_route"
    action: DesiredAction
    load_balancer_name: str
    listener_port: int
    listener_protocol: ListenerProtocol
    priority: int
    path_pattern: str | None = None
    host_header: str | None = None
    route_action: InboundRouteAction


class InboundTlsBinding(_InboundModel):
    change_type: Literal["tls_binding"] = "tls_binding"
    action: DesiredAction
    listener_arn: str
    certificate_arn: str
    default_certificate: bool = True


class InboundSecurityGroupRule(_InboundModel):
    change_type: Literal["security_group_rule"] = "security_group_rule"
    action: DesiredAction
    security_group_id: str
    direction: TrafficDirection
    protocol: IpProtocol
    from_port: int | None = None
    to_port: int | None = None
    cidr_blocks: list[str] = Field(default_factory=list)
    source_security_group_id: str | None = None
    description: str


InboundChangePayload = Annotated[
    InboundDnsRecord | InboundLoadBalancerRoute | InboundTlsBinding | InboundSecurityGroupRule,
    Field(discriminator="change_type"),
]


_FORBIDDEN_TOP_LEVEL_KEYS = frozenset(
    {
        "hcl",
        "terraform",
        "terraform_args",
        "tf_vars",
        "raw_hcl",
        "shell",
        "command",
        "commands",
        "aws_resource",
        "aws_resources",
        "resource",
        "resources",
        "config_blob",
        "unstructured",
        "extra",
    }
)


class InboundChangeRequest(_InboundModel):
    """Caller-submitted change request (API product contract)."""

    environment: Environment
    actor: str = Field(min_length=1, max_length=128)
    idempotency_key: IdempotencyKey | None = None
    change: InboundChangePayload

    @model_validator(mode="before")
    @classmethod
    def _reject_escape_hatches(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        forbidden = sorted(_FORBIDDEN_TOP_LEVEL_KEYS.intersection(data))
        if forbidden:
            raise DomainValidationError(
                "request contains forbidden unstructured/infrastructure fields: "
                + ", ".join(forbidden),
                field=forbidden[0],
            )
        change = data.get("change")
        if isinstance(change, dict):
            nested = sorted(_FORBIDDEN_TOP_LEVEL_KEYS.intersection(change))
            if nested:
                raise DomainValidationError(
                    "change payload contains forbidden unstructured fields: " + ", ".join(nested),
                    field=f"change.{nested[0]}",
                )
        return data
