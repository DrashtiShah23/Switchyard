"""HTTP API contract tests for Milestone 3."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.config import Settings
from app.repositories.sqlite import SqliteChangeRepository
from app.services.change_service import ChangeService
from tests.unit.conftest import dns_payload, lb_payload, sg_payload, tls_payload


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        env_name="local",
        database_url="sqlite:///:memory:",
        api_keys={"test-key": "alice", "other-key": "bob"},
        log_level="INFO",
    )
    service = ChangeService(SqliteChangeRepository(":memory:"))
    app = create_app(settings=settings, change_service=service)
    with TestClient(app) as test_client:
        yield test_client


def _auth(key: str = "test-key") -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_requires_auth(client: TestClient) -> None:
    response = client.post("/v1/changes", json=dns_payload())
    assert response.status_code == 401


def test_create_rejects_invalid_api_key(client: TestClient) -> None:
    response = client.post(
        "/v1/changes",
        json=dns_payload(),
        headers=_auth("wrong-key"),
    )
    assert response.status_code == 401


def test_create_and_get_change(client: TestClient) -> None:
    created = client.post("/v1/changes", json=dns_payload(), headers=_auth())
    assert created.status_code == 201
    body = created.json()
    request_id = body["request"]["request_id"]
    assert request_id.startswith("req_")
    assert body["request"]["state"] == "validated"
    assert body["request"]["actor"] == "alice"
    assert body["change_specification"]["change"]["change_kind"] == "dns_record"
    assert "hcl" not in body["change_specification"]

    fetched = client.get(f"/v1/changes/{request_id}", headers=_auth())
    assert fetched.status_code == 200
    assert fetched.json()["request_id"] == request_id


def test_create_rejects_domain_invalid_payload(client: TestClient) -> None:
    response = client.post(
        "/v1/changes",
        json=dns_payload(change={"values": ["not-an-ip"]}),
        headers=_auth(),
    )
    assert response.status_code == 422


def test_create_rejects_forbidden_hcl_field(client: TestClient) -> None:
    payload = dns_payload()
    payload["hcl"] = 'resource "aws_route53_record" {}'
    response = client.post("/v1/changes", json=payload, headers=_auth())
    assert response.status_code == 422


def test_idempotent_replay_same_request_id(client: TestClient) -> None:
    headers = {**_auth(), "Idempotency-Key": "client-1"}
    first = client.post("/v1/changes", json=dns_payload(), headers=headers)
    second = client.post("/v1/changes", json=dns_payload(), headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["request"]["request_id"] == second.json()["request"]["request_id"]


def test_idempotency_conflict(client: TestClient) -> None:
    headers = {**_auth(), "Idempotency-Key": "client-2"}
    assert (
        client.post(
            "/v1/changes",
            json=dns_payload(change={"name": "one.example.com"}),
            headers=headers,
        ).status_code
        == 201
    )
    conflict = client.post(
        "/v1/changes",
        json=dns_payload(change={"name": "two.example.com"}),
        headers=headers,
    )
    assert conflict.status_code == 409


def test_get_unknown_request(client: TestClient) -> None:
    response = client.get(f"/v1/changes/req_{'c' * 32}", headers=_auth())
    assert response.status_code == 404


def test_stage_stubs_not_available_yet(client: TestClient) -> None:
    created = client.post("/v1/changes", json=lb_payload(), headers=_auth())
    request_id = created.json()["request"]["request_id"]
    for stage in ("plan", "policy", "verification"):
        response = client.get(f"/v1/changes/{request_id}/{stage}", headers=_auth())
        assert response.status_code == 200
        body = response.json()
        assert body["available"] is False
        assert body["stage"] == stage
        assert body["state"] == "validated"


def test_handlers_do_not_accept_terraform_args(client: TestClient) -> None:
    payload = sg_payload()
    payload["terraform_args"] = ["-auto-approve"]
    response = client.post("/v1/changes", json=payload, headers=_auth())
    assert response.status_code == 422


def test_create_supports_all_change_types(client: TestClient) -> None:
    for payload in (dns_payload(), lb_payload(), tls_payload(), sg_payload()):
        response = client.post("/v1/changes", json=payload, headers=_auth())
        assert response.status_code == 201, response.text
        assert response.json()["request"]["state"] == "validated"
