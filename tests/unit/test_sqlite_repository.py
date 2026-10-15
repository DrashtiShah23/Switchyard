"""SQLite repository persistence tests."""

from __future__ import annotations

from app.domain.ids import IdempotencyKey
from app.domain.normalize import accept_change_request
from app.repositories.sqlite import SqliteChangeRepository
from tests.unit.conftest import dns_payload


def test_save_and_load_request_and_specification() -> None:
    repo = SqliteChangeRepository(":memory:")
    request, spec = accept_change_request(dns_payload(idempotency_key="k1"))
    repo.save(request, spec)

    loaded_request = repo.get_request(request.request_id)
    loaded_spec = repo.get_specification(request.request_id)
    assert loaded_request is not None
    assert loaded_spec is not None
    assert loaded_request.request_id == request.request_id
    assert loaded_spec.change_spec_id == spec.change_spec_id
    assert loaded_spec.to_dict()["change"]["change_kind"] == "dns_record"


def test_idempotency_lookup() -> None:
    repo = SqliteChangeRepository(":memory:")
    request, spec = accept_change_request(dns_payload(actor="alice", idempotency_key="idem-1"))
    repo.save(request, spec)

    found = repo.find_by_idempotency("alice", IdempotencyKey.parse("idem-1"))
    assert found is not None
    assert found[0].request_id == request.request_id
    assert repo.get_idempotency_fingerprint("alice", IdempotencyKey.parse("idem-1")) == str(
        spec.change_spec_id
    )
    assert repo.find_by_idempotency("bob", IdempotencyKey.parse("idem-1")) is None
