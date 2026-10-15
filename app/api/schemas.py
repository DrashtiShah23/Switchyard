"""HTTP response schemas. Request bodies are validated by the domain layer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "switchyard"


class ChangeRequestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    environment: str
    change_type: str
    actor: str
    state: str
    change_spec_id: str | None
    idempotency_key: str | None
    failure_reason: str | None
    created_at: str
    updated_at: str


class ChangeCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: ChangeRequestResponse
    change_specification: dict[str, Any] = Field(
        description="Normalized ChangeSpecification persisted for later Terraform use",
    )


class StageStubResponse(BaseModel):
    """Placeholder for plan/policy/verification until later milestones."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    state: str
    available: bool = False
    stage: str
    detail: str
