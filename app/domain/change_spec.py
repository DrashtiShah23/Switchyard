"""Normalized change specification — the only intent Terraform may consume."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.changes import DomainChange
from app.domain.enums import ChangeType, DeferredInventoryCheck, Environment
from app.domain.ids import ChangeSpecId, RequestId


class ChangeSpecification(BaseModel):
    """Typed, normalized infrastructure intent.

    Downstream Terraform rendering must consume this artifact (or an equivalent
    serialization of it). It must never consume raw API input, HCL strings, or
    unstructured configuration blobs.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    change_spec_id: ChangeSpecId
    request_id: RequestId
    environment: Environment
    change_type: ChangeType
    change: DomainChange
    schema_version: int = Field(default=1, ge=1)
    created_at: datetime
    deferred_checks: tuple[DeferredInventoryCheck, ...]

    def canonical_dict(self) -> dict[str, Any]:
        """Stable JSON-ready dict used for identity and serialization tests."""
        return {
            "schema_version": self.schema_version,
            "environment": self.environment.value,
            "change_type": self.change_type.value,
            "change": self.change.model_dump(mode="json"),
            "deferred_checks": [item.value for item in self.deferred_checks],
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_spec_id": str(self.change_spec_id),
            "request_id": str(self.request_id),
            "created_at": self.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            **self.canonical_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChangeSpecification:
        return cls.model_validate(data)


def deferred_checks_for(change_type: ChangeType) -> tuple[DeferredInventoryCheck, ...]:
    """Declare later-stage inventory checks without pretending they ran."""
    mapping: dict[ChangeType, tuple[DeferredInventoryCheck, ...]] = {
        ChangeType.DNS_RECORD: (
            DeferredInventoryCheck.DNS_DUPLICATE_OWNERSHIP,
            DeferredInventoryCheck.HOSTED_ZONE_EXISTS,
        ),
        ChangeType.LOAD_BALANCER_ROUTE: (DeferredInventoryCheck.LISTENER_EXISTS,),
        ChangeType.TLS_BINDING: (
            DeferredInventoryCheck.CERTIFICATE_EXISTS,
            DeferredInventoryCheck.LISTENER_EXISTS,
        ),
        ChangeType.SECURITY_GROUP_RULE: (
            DeferredInventoryCheck.SECURITY_GROUP_EXISTS,
            DeferredInventoryCheck.CIDR_OVERLAP_WITH_LIVE_SG,
        ),
    }
    return mapping[change_type]
