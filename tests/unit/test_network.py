"""Network semantic validation without AWS."""

from __future__ import annotations

import pytest

from app.domain.enums import DnsRecordType, IpProtocol, ListenerProtocol
from app.domain.errors import DomainValidationError
from app.domain.network import (
    validate_cidr,
    validate_dns_name,
    validate_dns_record_values,
    validate_listener_port,
    validate_port,
    validate_port_range,
    validate_sg_protocol_ports,
    validate_ttl,
)


@pytest.mark.parametrize("value", ["10.0.0.0/8", "192.168.1.0/24", "2001:db8::/32"])
def test_valid_cidrs(value: str) -> None:
    assert validate_cidr(value) == value


@pytest.mark.parametrize("value", ["10.0.0.1/33", "not-a-cidr", "10.0.0.0/8 ", "10.0.0.1/24"])
def test_invalid_cidrs(value: str) -> None:
    # host bits set (strict) and bad prefixes should fail
    with pytest.raises(DomainValidationError):
        validate_cidr(value)


@pytest.mark.parametrize("port", [1, 80, 443, 65535])
def test_valid_ports(port: int) -> None:
    assert validate_port(port, field="port") == port


@pytest.mark.parametrize("port", [0, -1, 65536, True])
def test_invalid_ports(port: object) -> None:
    with pytest.raises(DomainValidationError):
        validate_port(port, field="port")  # type: ignore[arg-type]


def test_port_range_order() -> None:
    validate_port_range(80, 90)
    with pytest.raises(DomainValidationError):
        validate_port_range(90, 80)


@pytest.mark.parametrize("name", ["app.example.com", "api", "a.b.c.example.com."])
def test_valid_dns_names(name: str) -> None:
    assert "." not in validate_dns_name(name) or True
    result = validate_dns_name(name)
    assert not result.endswith(".")


@pytest.mark.parametrize("name", ["", "-bad.example.com", "bad..example.com", "*.example.com"])
def test_invalid_dns_names(name: str) -> None:
    with pytest.raises(DomainValidationError):
        validate_dns_name(name)


def test_dns_record_values_by_type() -> None:
    assert validate_dns_record_values(DnsRecordType.A, ["1.2.3.4"]) == ["1.2.3.4"]
    assert validate_dns_record_values(DnsRecordType.AAAA, ["2001:db8::1"])
    assert validate_dns_record_values(DnsRecordType.CNAME, ["target.example.com"]) == [
        "target.example.com"
    ]
    assert validate_dns_record_values(DnsRecordType.TXT, ["v=spf1 -all"]) == ["v=spf1 -all"]


def test_dns_record_value_contradictions() -> None:
    with pytest.raises(DomainValidationError):
        validate_dns_record_values(DnsRecordType.A, ["not-an-ip"])
    with pytest.raises(DomainValidationError):
        validate_dns_record_values(DnsRecordType.CNAME, ["a.example.com", "b.example.com"])
    with pytest.raises(DomainValidationError):
        validate_dns_record_values(DnsRecordType.A, [])


def test_ttl_bounds() -> None:
    assert validate_ttl(60) == 60
    assert validate_ttl(172800) == 172800
    with pytest.raises(DomainValidationError):
        validate_ttl(59)
    with pytest.raises(DomainValidationError):
        validate_ttl(172801)


def test_listener_port_protocol_semantics() -> None:
    assert validate_listener_port(80, ListenerProtocol.HTTP) == 80
    assert validate_listener_port(443, ListenerProtocol.HTTPS) == 443
    with pytest.raises(DomainValidationError):
        validate_listener_port(443, ListenerProtocol.HTTP)
    with pytest.raises(DomainValidationError):
        validate_listener_port(80, ListenerProtocol.HTTPS)


def test_sg_protocol_port_rules() -> None:
    assert validate_sg_protocol_ports(IpProtocol.TCP, 443, 443) == (443, 443)
    assert validate_sg_protocol_ports(IpProtocol.ALL, None, None) == (None, None)
    assert validate_sg_protocol_ports(IpProtocol.ICMP, None, None) == (None, None)
    assert validate_sg_protocol_ports(IpProtocol.ICMP, 8, 0) == (8, 0)
    with pytest.raises(DomainValidationError):
        validate_sg_protocol_ports(IpProtocol.TCP, None, None)
    with pytest.raises(DomainValidationError):
        validate_sg_protocol_ports(IpProtocol.ALL, 1, 1)
    with pytest.raises(DomainValidationError):
        validate_sg_protocol_ports(IpProtocol.ICMP, 8, None)
