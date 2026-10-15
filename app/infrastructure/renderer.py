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
from app.domain.changes import DnsRecordChange, SecurityGroupRuleChange
from app.domain.enums import DesiredAction, IpProtocol, TrafficDirection
from app.domain.errors import DomainValidationError


class RenderContext(BaseModel):
    """Environment-bound values that callers cannot invent as free-form infra."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hosted_zone_id: str | None = None


class TerraformModuleInput(BaseModel):
    """Typed module invocation request produced from a ChangeSpecification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    module_name: Literal["dns", "security_group"]
    variables: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_name": self.module_name,
            "variables": self.variables,
        }

    def canonical_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class UnsupportedChangeForRenderer(DomainValidationError):
    """Change type is valid in domain but not rendered in this milestone."""


class ChangeSpecificationRenderer:
    """Map ChangeSpecification → module inputs for DNS and security group rules."""

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
        raise UnsupportedChangeForRenderer(
            f"renderer does not support change_kind={change.change_kind!r} in Milestone 5",
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
        # hosted_zone_name is informational on the domain model; zone ownership
        # for Terraform is always the environment-bound zone_id.
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
            # One Terraform rule resource per CIDR keeps ownership explicit.
            # For a single CIDR (common case) emit one rule; multiple CIDRs expand.
            rules = [
                {
                    **rule,
                    "cidr_ipv4": cidr,
                }
                for cidr in change.cidr_blocks
            ]
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

    @staticmethod
    def _aws_protocol(protocol: IpProtocol) -> str:
        if protocol is IpProtocol.ALL:
            return "-1"
        return protocol.value
