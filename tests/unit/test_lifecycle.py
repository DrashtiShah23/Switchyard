"""Lifecycle state machine: every legal transition and representative illegal ones."""

from __future__ import annotations

import pytest

from app.domain.enums import LifecycleEvent, LifecycleState
from app.domain.errors import IllegalTransitionError
from app.domain.lifecycle import (
    all_legal_transitions,
    allowed_events,
    can_transition,
    is_terminal,
    transition,
)

EXPECTED_TRANSITIONS: set[tuple[LifecycleState, LifecycleEvent, LifecycleState]] = {
    (LifecycleState.REQUESTED, LifecycleEvent.VALIDATION_SUCCEEDED, LifecycleState.VALIDATED),
    (LifecycleState.REQUESTED, LifecycleEvent.VALIDATION_FAILED, LifecycleState.FAILED),
    (LifecycleState.VALIDATED, LifecycleEvent.PLAN_SUCCEEDED, LifecycleState.PLANNED),
    (LifecycleState.VALIDATED, LifecycleEvent.PLAN_FAILED, LifecycleState.FAILED),
    (LifecycleState.PLANNED, LifecycleEvent.POLICY_PASSED, LifecycleState.AWAITING_APPROVAL),
    (LifecycleState.PLANNED, LifecycleEvent.POLICY_REJECTED, LifecycleState.POLICY_REJECTED),
    (LifecycleState.PLANNED, LifecycleEvent.POLICY_ENGINE_FAILED, LifecycleState.FAILED),
    (LifecycleState.AWAITING_APPROVAL, LifecycleEvent.APPLY_STARTED, LifecycleState.APPLYING),
    (LifecycleState.AWAITING_APPROVAL, LifecycleEvent.ABANDONED, LifecycleState.FAILED),
    (LifecycleState.APPLYING, LifecycleEvent.APPLY_SUCCEEDED, LifecycleState.VERIFYING),
    (LifecycleState.APPLYING, LifecycleEvent.APPLY_FAILED, LifecycleState.FAILED),
    (LifecycleState.VERIFYING, LifecycleEvent.VERIFICATION_SUCCEEDED, LifecycleState.SUCCEEDED),
    (LifecycleState.VERIFYING, LifecycleEvent.VERIFICATION_FAILED, LifecycleState.FAILED),
}


@pytest.mark.parametrize(("current", "event", "expected"), sorted(EXPECTED_TRANSITIONS))
def test_every_legal_transition(
    current: LifecycleState,
    event: LifecycleEvent,
    expected: LifecycleState,
) -> None:
    assert can_transition(current, event)
    assert transition(current, event) is expected


def test_all_legal_transitions_matches_expected_table() -> None:
    assert all_legal_transitions() == frozenset(EXPECTED_TRANSITIONS)


@pytest.mark.parametrize(
    ("current", "event"),
    [
        (LifecycleState.REQUESTED, LifecycleEvent.PLAN_SUCCEEDED),
        (LifecycleState.REQUESTED, LifecycleEvent.APPLY_STARTED),
        (LifecycleState.VALIDATED, LifecycleEvent.VALIDATION_SUCCEEDED),
        (LifecycleState.VALIDATED, LifecycleEvent.POLICY_PASSED),
        (LifecycleState.PLANNED, LifecycleEvent.APPLY_STARTED),
        (LifecycleState.PLANNED, LifecycleEvent.VALIDATION_SUCCEEDED),
        (LifecycleState.AWAITING_APPROVAL, LifecycleEvent.POLICY_PASSED),
        (LifecycleState.AWAITING_APPROVAL, LifecycleEvent.VERIFICATION_SUCCEEDED),
        (LifecycleState.APPLYING, LifecycleEvent.PLAN_SUCCEEDED),
        (LifecycleState.APPLYING, LifecycleEvent.APPLY_STARTED),
        (LifecycleState.VERIFYING, LifecycleEvent.APPLY_SUCCEEDED),
        (LifecycleState.SUCCEEDED, LifecycleEvent.VALIDATION_SUCCEEDED),
        (LifecycleState.FAILED, LifecycleEvent.PLAN_SUCCEEDED),
        (LifecycleState.POLICY_REJECTED, LifecycleEvent.POLICY_PASSED),
        (LifecycleState.POLICY_REJECTED, LifecycleEvent.ABANDONED),
        (LifecycleState.SUCCEEDED, LifecycleEvent.ABANDONED),
    ],
)
def test_representative_illegal_transitions(
    current: LifecycleState,
    event: LifecycleEvent,
) -> None:
    assert not can_transition(current, event)
    with pytest.raises(IllegalTransitionError) as exc_info:
        transition(current, event)
    assert exc_info.value.current_state == current.value
    assert exc_info.value.event == event.value


def test_terminal_states() -> None:
    assert is_terminal(LifecycleState.SUCCEEDED)
    assert is_terminal(LifecycleState.FAILED)
    assert is_terminal(LifecycleState.POLICY_REJECTED)
    assert not is_terminal(LifecycleState.AWAITING_APPROVAL)
    assert not is_terminal(LifecycleState.REQUESTED)


def test_allowed_events_for_planned() -> None:
    assert allowed_events(LifecycleState.PLANNED) == frozenset(
        {
            LifecycleEvent.POLICY_PASSED,
            LifecycleEvent.POLICY_REJECTED,
            LifecycleEvent.POLICY_ENGINE_FAILED,
        }
    )


def test_allowed_events_empty_for_terminal() -> None:
    assert allowed_events(LifecycleState.SUCCEEDED) == frozenset()
    assert allowed_events(LifecycleState.FAILED) == frozenset()
    assert allowed_events(LifecycleState.POLICY_REJECTED) == frozenset()
