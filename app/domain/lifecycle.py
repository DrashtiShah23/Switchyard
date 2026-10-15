"""Explicit lifecycle state machine for change requests."""

from __future__ import annotations

from app.domain.enums import LifecycleEvent, LifecycleState
from app.domain.errors import IllegalTransitionError

# (current_state, event) -> next_state
_TRANSITIONS: dict[tuple[LifecycleState, LifecycleEvent], LifecycleState] = {
    (LifecycleState.REQUESTED, LifecycleEvent.VALIDATION_SUCCEEDED): LifecycleState.VALIDATED,
    (LifecycleState.REQUESTED, LifecycleEvent.VALIDATION_FAILED): LifecycleState.FAILED,
    (LifecycleState.VALIDATED, LifecycleEvent.PLAN_SUCCEEDED): LifecycleState.PLANNED,
    (LifecycleState.VALIDATED, LifecycleEvent.PLAN_FAILED): LifecycleState.FAILED,
    (LifecycleState.PLANNED, LifecycleEvent.POLICY_PASSED): LifecycleState.AWAITING_APPROVAL,
    (LifecycleState.PLANNED, LifecycleEvent.POLICY_REJECTED): LifecycleState.POLICY_REJECTED,
    (LifecycleState.PLANNED, LifecycleEvent.POLICY_ENGINE_FAILED): LifecycleState.FAILED,
    (LifecycleState.AWAITING_APPROVAL, LifecycleEvent.APPLY_STARTED): LifecycleState.APPLYING,
    (LifecycleState.AWAITING_APPROVAL, LifecycleEvent.ABANDONED): LifecycleState.FAILED,
    (LifecycleState.APPLYING, LifecycleEvent.APPLY_SUCCEEDED): LifecycleState.VERIFYING,
    (LifecycleState.APPLYING, LifecycleEvent.APPLY_FAILED): LifecycleState.FAILED,
    (LifecycleState.VERIFYING, LifecycleEvent.VERIFICATION_SUCCEEDED): LifecycleState.SUCCEEDED,
    (LifecycleState.VERIFYING, LifecycleEvent.VERIFICATION_FAILED): LifecycleState.FAILED,
}

_TERMINAL_STATES: frozenset[LifecycleState] = frozenset(
    {
        LifecycleState.POLICY_REJECTED,
        LifecycleState.SUCCEEDED,
        LifecycleState.FAILED,
    }
)


def is_terminal(state: LifecycleState) -> bool:
    return state in _TERMINAL_STATES


def allowed_events(state: LifecycleState) -> frozenset[LifecycleEvent]:
    return frozenset(event for (current, event) in _TRANSITIONS if current is state)


def can_transition(current: LifecycleState, event: LifecycleEvent) -> bool:
    return (current, event) in _TRANSITIONS


def transition(current: LifecycleState, event: LifecycleEvent) -> LifecycleState:
    """Apply a lifecycle event or raise IllegalTransitionError."""
    try:
        return _TRANSITIONS[(current, event)]
    except KeyError as exc:
        raise IllegalTransitionError(
            f"cannot apply {event.value!r} from state {current.value!r}",
            current_state=current.value,
            event=event.value,
        ) from exc


def all_legal_transitions() -> frozenset[tuple[LifecycleState, LifecycleEvent, LifecycleState]]:
    return frozenset((current, event, nxt) for (current, event), nxt in _TRANSITIONS.items())
