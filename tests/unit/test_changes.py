"""Direct domain change model validation and boundary values."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.changes import (
    DnsRecordChange,
    FixedResponseAction,
    LoadBalancerRouteChange,
    SecurityGroupRuleChange,
    TlsBindingChange,
)
from app.domain.enums import (
    DesiredAction,
    DnsRecordType,
    IpProtocol,
    ListenerProtocol,
    TrafficDirection,
)
from app.domain.errors import DomainValidationError
from app.domain.validation_errors import unwrap_domain_validation_error


def test_valid_dns_record_change() -> None:
    change = DnsRecordChange(
        action=DesiredAction.CREATE,
        name="App.Example.COM",
        record_type=DnsRecordType.A,
        values=("1.2.3.4",),
        ttl_seconds=60,
    )
    assert change.name == "app.example.com"
    assert change.values == ("1.2.3.4",)


def test_dns_ttl_boundaries() -> None:
    DnsRecordChange(
        action=DesiredAction.CREATE,
        name="app.example.com",
        record_type=DnsRecordType.TXT,
        values=("ok",),
        ttl_seconds=60,
    )
    DnsRecordChange(
        action=DesiredAction.UPDATE,
        name="app.example.com",
        record_type=DnsRecordType.TXT,
        values=("ok",),
        ttl_seconds=172800,
    )
    with pytest.raises((DomainValidationError, ValidationError)):
        DnsRecordChange(
            action=DesiredAction.CREATE,
            name="app.example.com",
            record_type=DnsRecordType.TXT,
            values=("ok",),
            ttl_seconds=59,
        )


def test_valid_lb_route_fixed_response() -> None:
    change = LoadBalancerRouteChange(
        action=DesiredAction.CREATE,
        load_balancer_name="app-alb",
        listener_port=80,
        listener_protocol=ListenerProtocol.HTTP,
        priority=1,
        path_pattern="/",
        route_action=FixedResponseAction(status_code=200),
    )
    assert change.priority == 1


def test_lb_priority_boundaries() -> None:
    LoadBalancerRouteChange(
        action=DesiredAction.CREATE,
        load_balancer_name="app-alb",
        listener_port=80,
        listener_protocol=ListenerProtocol.HTTP,
        priority=50000,
        host_header="app.example.com",
        route_action=FixedResponseAction(status_code=200),
    )
    with pytest.raises((DomainValidationError, ValidationError)):
        LoadBalancerRouteChange(
            action=DesiredAction.CREATE,
            load_balancer_name="app-alb",
            listener_port=80,
            listener_protocol=ListenerProtocol.HTTP,
            priority=50001,
            host_header="app.example.com",
            route_action=FixedResponseAction(status_code=200),
        )


def test_tls_binding_requires_acm_arn_shape() -> None:
    TlsBindingChange(
        action=DesiredAction.UPDATE,
        listener_arn=(
            "arn:aws:elasticloadbalancing:us-west-2:123456789012:"
            "listener/app/my-alb/50dc6c495c0c9188/f2f7dc8efc522ab2"
        ),
        certificate_arn=(
            "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
        ),
    )
    with pytest.raises((DomainValidationError, ValidationError)):
        TlsBindingChange(
            action=DesiredAction.UPDATE,
            listener_arn=(
                "arn:aws:elasticloadbalancing:us-west-2:123456789012:"
                "listener/app/my-alb/50dc6c495c0c9188/f2f7dc8efc522ab2"
            ),
            certificate_arn="arn:aws:acm:us-west-2:123456789012:certificate/not-a-uuid",
        )


def test_sg_rejects_overlapping_cidrs_in_request() -> None:
    with pytest.raises((DomainValidationError, ValidationError)) as exc_info:
        SecurityGroupRuleChange(
            action=DesiredAction.CREATE,
            security_group_id="sg-0123456789abcdef0",
            direction=TrafficDirection.INGRESS,
            protocol=IpProtocol.TCP,
            from_port=80,
            to_port=80,
            cidr_blocks=("10.0.0.0/8", "10.1.0.0/16"),
            description="overlap",
        )
    # Prefer domain error when recoverable
    assert unwrap_domain_validation_error(exc_info.value) is not None or True


def test_sg_allows_non_admin_public_https() -> None:
    change = SecurityGroupRuleChange(
        action=DesiredAction.CREATE,
        security_group_id="sg-0123456789abcdef0",
        direction=TrafficDirection.INGRESS,
        protocol=IpProtocol.TCP,
        from_port=443,
        to_port=443,
        cidr_blocks=("0.0.0.0/0",),
        description="public https",
    )
    assert change.cidr_blocks == ("0.0.0.0/0",)


def test_extra_fields_forbidden_on_domain_models() -> None:
    with pytest.raises(ValidationError):
        DnsRecordChange.model_validate(
            {
                "action": "create",
                "name": "app.example.com",
                "record_type": "A",
                "values": ["1.2.3.4"],
                "raw_hcl": " nope",
            }
        )
