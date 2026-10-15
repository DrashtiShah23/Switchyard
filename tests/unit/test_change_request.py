"""ChangeRequest aggregate lifecycle enforcement."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.change_request import ChangeRequest
from app.domain.enums import ChangeType, Environment, LifecycleEvent, LifecycleState
from app.domain.errors import IllegalTransitionError
from app.domain.ids import RequestId
from app.domain.lifecycle import all_legal_transitions


def _request(state: LifecycleState = LifecycleState.REQUESTED) -> ChangeRequest:
    now = datetime.now(UTC)
    return ChangeRequest(
        request_id=RequestId.generate(),
        environment=Environment.DEV,
        change_type=ChangeType.DNS_RECORD,
        actor="alice",
        state=state,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.parametrize(("current", "event", "expected"), sorted(all_legal_transitions()))
def test_change_request_apply_all_legal_transitions(
    current: LifecycleState,
    event: LifecycleEvent,
    expected: LifecycleState,
) -> None:
    updated = _request(current).apply(event)
    assert updated.state is expected
    if expected is LifecycleState.FAILED:
        assert updated.failure_reason is not None
    else:
        assert updated.failure_reason is None


def test_change_request_rejects_illegal_transition() -> None:
    req = _request(LifecycleState.REQUESTED)
    with pytest.raises(IllegalTransitionError):
        req.apply(LifecycleEvent.APPLY_STARTED)


def test_terminal_states_cannot_transition() -> None:
    for state in (
        LifecycleState.SUCCEEDED,
        LifecycleState.FAILED,
        LifecycleState.POLICY_REJECTED,
    ):
        req = _request(state)
        with pytest.raises(IllegalTransitionError):
            req.apply(LifecycleEvent.ABANDONED)


def test_happy_path_sequence() -> None:
    req = _request()
    req = req.apply(LifecycleEvent.VALIDATION_SUCCEEDED)
    req = req.apply(LifecycleEvent.PLAN_SUCCEEDED)
    req = req.apply(LifecycleEvent.POLICY_PASSED)
    assert req.state is LifecycleState.AWAITING_APPROVAL
    req = req.apply(LifecycleEvent.APPLY_STARTED)
    req = req.apply(LifecycleEvent.APPLY_SUCCEEDED)
    req = req.apply(LifecycleEvent.VERIFICATION_SUCCEEDED)
    assert req.state is LifecycleState.SUCCEEDED


def test_policy_rejection_path() -> None:
    req = (
        _request()
        .apply(LifecycleEvent.VALIDATION_SUCCEEDED)
        .apply(LifecycleEvent.PLAN_SUCCEEDED)
        .apply(LifecycleEvent.POLICY_REJECTED)
    )
    assert req.state is LifecycleState.POLICY_REJECTED
    with pytest.raises(IllegalTransitionError):
        req.apply(LifecycleEvent.APPLY_STARTED)
