"""Change request aggregate with enforced lifecycle transitions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ChangeType, Environment, LifecycleEvent, LifecycleState
from app.domain.errors import IllegalTransitionError
from app.domain.ids import ChangeSpecId, IdempotencyKey, RequestId
from app.domain.lifecycle import is_terminal, transition


class ChangeRequest(BaseModel):
    """Durable request record (domain form). Persistence lands in Milestone 3."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: RequestId
    environment: Environment
    change_type: ChangeType
    actor: str = Field(min_length=1, max_length=128)
    state: LifecycleState
    change_spec_id: ChangeSpecId | None = None
    idempotency_key: IdempotencyKey | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    def apply(self, event: LifecycleEvent, *, failure_reason: str | None = None) -> Self:
        """Return a new ChangeRequest after a legal lifecycle transition."""
        if is_terminal(self.state):
            raise IllegalTransitionError(
                f"cannot apply {event.value!r} from terminal state {self.state.value!r}",
                current_state=self.state.value,
                event=event.value,
            )
        new_state = transition(self.state, event)
        reason = failure_reason if new_state is LifecycleState.FAILED else None
        if new_state is LifecycleState.FAILED and not reason:
            reason = f"failed on event {event.value}"
        return self.model_copy(
            update={
                "state": new_state,
                "failure_reason": reason,
                "updated_at": datetime.now(UTC),
            }
        )

    def with_change_spec_id(self, change_spec_id: ChangeSpecId) -> Self:
        return self.model_copy(
            update={
                "change_spec_id": change_spec_id,
                "updated_at": datetime.now(UTC),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "environment": self.environment.value,
            "change_type": self.change_type.value,
            "actor": self.actor,
            "state": self.state.value,
            "change_spec_id": str(self.change_spec_id) if self.change_spec_id else None,
            "idempotency_key": str(self.idempotency_key) if self.idempotency_key else None,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "updated_at": self.updated_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChangeRequest:
        return cls.model_validate(data)
