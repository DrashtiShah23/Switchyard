"""Stable identifier value objects."""

from __future__ import annotations

import pytest

from app.domain.errors import DomainValidationError
from app.domain.ids import ChangeSpecId, IdempotencyKey, RequestId


def test_request_id_generate_and_parse() -> None:
    rid = RequestId.generate()
    assert rid.startswith("req_")
    assert len(rid) == 36
    assert RequestId.parse(str(rid)) == rid


@pytest.mark.parametrize("bad", ["", "req_", "req_xyz", "request_1", "REQ_" + "a" * 32])
def test_request_id_rejects_invalid(bad: str) -> None:
    with pytest.raises(DomainValidationError):
        RequestId.parse(bad)


def test_change_spec_id_is_content_addressed_and_stable() -> None:
    payload = {"environment": "dev", "change_type": "dns_record", "x": 1}
    a = ChangeSpecId.from_canonical_payload(payload)
    b = ChangeSpecId.from_canonical_payload(payload)
    c = ChangeSpecId.from_canonical_payload({**payload, "x": 2})
    assert a == b
    assert a != c
    assert a.startswith("spec_")
    assert ChangeSpecId.parse(str(a)) == a


def test_idempotency_key_accepts_valid() -> None:
    key = IdempotencyKey.parse("client-key:abc_123.v1")
    assert key == "client-key:abc_123.v1"


@pytest.mark.parametrize("bad", ["", "has space", "bad/slash", "x" * 129])
def test_idempotency_key_rejects_invalid(bad: str) -> None:
    with pytest.raises(DomainValidationError):
        IdempotencyKey.parse(bad)
