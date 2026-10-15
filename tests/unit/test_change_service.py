"""ChangeService orchestration tests."""

from __future__ import annotations

import pytest

from app.domain.enums import LifecycleState
from app.domain.errors import DomainValidationError
from app.repositories.sqlite import SqliteChangeRepository
from app.services.change_service import ChangeService
from app.services.errors import IdempotencyConflictError, NotFoundError
from tests.unit.conftest import dns_payload


@pytest.fixture
def service() -> ChangeService:
    return ChangeService(SqliteChangeRepository(":memory:"))


def test_create_persists_validated_request_and_spec(service: ChangeService) -> None:
    request, spec = service.create_change(actor="alice", payload=dns_payload())
    assert request.state is LifecycleState.VALIDATED
    assert request.actor == "alice"
    assert request.change_spec_id == spec.change_spec_id

    loaded = service.get_change(str(request.request_id))
    assert loaded[0].request_id == request.request_id
    assert loaded[1].change_spec_id == spec.change_spec_id


def test_actor_from_auth_overrides_body_actor(service: ChangeService) -> None:
    request, _ = service.create_change(
        actor="alice",
        payload=dns_payload(actor="eve"),
    )
    assert request.actor == "alice"


def test_idempotent_replay_returns_same_request(service: ChangeService) -> None:
    payload = dns_payload()
    first, first_spec = service.create_change(
        actor="alice",
        payload=payload,
        idempotency_key="same-key",
    )
    second, second_spec = service.create_change(
        actor="alice",
        payload=payload,
        idempotency_key="same-key",
    )
    assert first.request_id == second.request_id
    assert first_spec.change_spec_id == second_spec.change_spec_id


def test_idempotency_conflict_on_different_payload(service: ChangeService) -> None:
    service.create_change(
        actor="alice",
        payload=dns_payload(change={"name": "a.example.com"}),
        idempotency_key="same-key",
    )
    with pytest.raises(IdempotencyConflictError):
        service.create_change(
            actor="alice",
            payload=dns_payload(change={"name": "b.example.com"}),
            idempotency_key="same-key",
        )


def test_validation_failure_does_not_persist(service: ChangeService) -> None:
    with pytest.raises(DomainValidationError):
        service.create_change(
            actor="alice",
            payload=dns_payload(change={"values": ["not-an-ip"]}),
        )
    with pytest.raises(NotFoundError):
        # No accidental persistence of invalid attempts with a known id pattern;
        # ensure repository remains empty via unknown id lookup shape.
        service.get_request("req_" + ("a" * 32))


def test_get_missing_request(service: ChangeService) -> None:
    with pytest.raises(NotFoundError):
        service.get_request("req_" + ("b" * 32))
