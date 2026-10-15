"""Normalization: inbound → domain change → ChangeSpecification."""

from __future__ import annotations

import pytest

from app.domain.enums import (
    ChangeType,
    DeferredInventoryCheck,
    Environment,
    LifecycleState,
)
from app.domain.errors import DomainValidationError
from app.domain.ids import RequestId
from app.domain.normalize import accept_change_request, parse_inbound
from tests.unit.conftest import dns_payload, lb_payload, sg_payload, tls_payload


@pytest.mark.parametrize(
    ("payload", "change_type", "environment"),
    [
        (dns_payload(), ChangeType.DNS_RECORD, Environment.DEV),
        (lb_payload(), ChangeType.LOAD_BALANCER_ROUTE, Environment.DEV),
        (tls_payload(), ChangeType.TLS_BINDING, Environment.STAGING),
        (sg_payload(), ChangeType.SECURITY_GROUP_RULE, Environment.PROD),
    ],
)
def test_accept_valid_change_types(
    payload: dict,
    change_type: ChangeType,
    environment: Environment,
) -> None:
    request, spec = accept_change_request(payload, request_id=RequestId.generate())
    assert request.state is LifecycleState.VALIDATED
    assert request.environment is environment
    assert request.change_type is change_type
    assert spec.change_type is change_type
    assert spec.request_id == request.request_id
    assert request.change_spec_id == spec.change_spec_id
    assert spec.change_spec_id.startswith("spec_")


def test_change_specification_is_distinct_typed_artifact() -> None:
    _, spec = accept_change_request(dns_payload())
    dumped = spec.to_dict()
    assert "hcl" not in dumped
    assert "terraform" not in dumped
    assert dumped["change"]["change_kind"] == "dns_record"
    assert isinstance(dumped["change"]["values"], list)
    round_trip = type(spec).from_dict(dumped)
    assert round_trip.change_spec_id == spec.change_spec_id
    assert round_trip.canonical_dict() == spec.canonical_dict()


def test_identical_intent_yields_identical_change_spec_id() -> None:
    rid1 = RequestId.generate()
    rid2 = RequestId.generate()
    _, spec1 = accept_change_request(dns_payload(), request_id=rid1)
    _, spec2 = accept_change_request(dns_payload(), request_id=rid2)
    assert rid1 != rid2
    assert spec1.change_spec_id == spec2.change_spec_id


def test_idempotency_key_preserved_on_request() -> None:
    payload = dns_payload(idempotency_key="client-1")
    request, _ = accept_change_request(payload)
    assert request.idempotency_key == "client-1"


def test_deferred_checks_declared_not_pretended() -> None:
    _, dns_spec = accept_change_request(dns_payload())
    assert DeferredInventoryCheck.DNS_DUPLICATE_OWNERSHIP in dns_spec.deferred_checks
    assert DeferredInventoryCheck.HOSTED_ZONE_EXISTS in dns_spec.deferred_checks

    _, sg_spec = accept_change_request(sg_payload())
    assert DeferredInventoryCheck.CIDR_OVERLAP_WITH_LIVE_SG in sg_spec.deferred_checks
    assert DeferredInventoryCheck.SECURITY_GROUP_EXISTS in sg_spec.deferred_checks


def test_unknown_environment_rejected() -> None:
    with pytest.raises(DomainValidationError):
        parse_inbound(dns_payload(environment="qa"))


def test_forbidden_unstructured_fields_rejected() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        parse_inbound(dns_payload(hcl='resource "aws_route53_record" {}'))
    assert "forbidden" in str(exc_info.value).lower() or "hcl" in str(exc_info.value).lower()

    with pytest.raises(DomainValidationError):
        parse_inbound(dns_payload(change={"terraform_args": ["-auto-approve"]}))


@pytest.mark.parametrize(
    "payload",
    [
        dns_payload(change={"name": "-bad.example.com"}),
        dns_payload(change={"record_type": "A", "values": ["not-an-ip"]}),
        dns_payload(change={"record_type": "CNAME", "values": ["a.com", "b.com"]}),
        dns_payload(change={"ttl_seconds": 30}),
        lb_payload(change={"listener_protocol": "HTTP", "listener_port": 443}),
        lb_payload(change={"path_pattern": None, "host_header": None}),
        lb_payload(change={"priority": 0}),
        tls_payload(change={"certificate_arn": "not-an-arn"}),
        sg_payload(change={"cidr_blocks": ["10.0.0.1/24"]}),
        sg_payload(change={"from_port": 443, "to_port": 80}),
        sg_payload(
            change={
                "cidr_blocks": ["0.0.0.0/0"],
                "protocol": "tcp",
                "from_port": 22,
                "to_port": 22,
                "description": "ssh open",
            }
        ),
        sg_payload(
            change={
                "cidr_blocks": ["10.0.0.0/8"],
                "source_security_group_id": "sg-0123456789abcdef0",
            }
        ),
        sg_payload(change={"cidr_blocks": [], "source_security_group_id": None}),
    ],
)
def test_invalid_inputs_rejected_with_domain_error(payload: dict) -> None:
    with pytest.raises(DomainValidationError):
        accept_change_request(payload)


def test_serialization_round_trip_request() -> None:
    request, _ = accept_change_request(dns_payload())
    restored = type(request).from_dict(request.to_dict())
    assert restored.request_id == request.request_id
    assert restored.state is request.state
    assert restored.idempotency_key == request.idempotency_key
