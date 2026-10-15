"""Network semantic helpers that do not require AWS."""

from __future__ import annotations

import ipaddress
import re

from app.domain.enums import DnsRecordType, IpProtocol, ListenerProtocol
from app.domain.errors import DomainValidationError

# Relative or FQDN hostname: labels 1-63, total <= 253, optional trailing dot.
_DNS_NAME_RE = re.compile(
    r"^(?=.{1,253}\.?$)"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.?$"
)

_ACM_CERT_ARN_RE = re.compile(
    r"^arn:aws:acm:[a-z0-9-]+:\d{12}:certificate/"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)

_SG_ID_RE = re.compile(r"^sg-[0-9a-f]{8,17}$")
_LISTENER_ARN_RE = re.compile(r"^arn:aws:elasticloadbalancing:[a-z0-9-]+:\d{12}:listener/.+$")


def validate_port(port: int, *, field: str) -> int:
    if not isinstance(port, int) or isinstance(port, bool):
        raise DomainValidationError(f"{field} must be an integer", field=field)
    if port < 1 or port > 65535:
        raise DomainValidationError(
            f"{field} must be between 1 and 65535 inclusive",
            field=field,
        )
    return port


def validate_port_range(from_port: int, to_port: int, *, field_prefix: str = "port") -> None:
    validate_port(from_port, field=f"{field_prefix}_from")
    validate_port(to_port, field=f"{field_prefix}_to")
    if from_port > to_port:
        raise DomainValidationError(
            f"{field_prefix}_from must be <= {field_prefix}_to",
            field=f"{field_prefix}_from",
        )


def validate_cidr(value: str, *, field: str = "cidr") -> str:
    try:
        network = ipaddress.ip_network(value, strict=True)
    except ValueError as exc:
        raise DomainValidationError(
            f"invalid CIDR {value!r}: {exc}",
            field=field,
        ) from exc
    return str(network)


def validate_dns_name(name: str, *, field: str = "name") -> str:
    normalized = name.strip().lower()
    if not normalized or not _DNS_NAME_RE.fullmatch(normalized):
        raise DomainValidationError(
            f"invalid DNS name {name!r}",
            field=field,
        )
    if ".." in normalized:
        raise DomainValidationError(f"invalid DNS name {name!r}", field=field)
    return normalized.rstrip(".")


def validate_ipv4_address(value: str, *, field: str = "value") -> str:
    try:
        addr = ipaddress.IPv4Address(value)
    except ValueError as exc:
        raise DomainValidationError(
            f"invalid IPv4 address {value!r}",
            field=field,
        ) from exc
    return str(addr)


def validate_ipv6_address(value: str, *, field: str = "value") -> str:
    try:
        addr = ipaddress.IPv6Address(value)
    except ValueError as exc:
        raise DomainValidationError(
            f"invalid IPv6 address {value!r}",
            field=field,
        ) from exc
    return str(addr)


def validate_dns_record_values(record_type: DnsRecordType, values: list[str]) -> list[str]:
    if not values:
        raise DomainValidationError("DNS values must not be empty", field="values")
    if record_type is DnsRecordType.CNAME and len(values) != 1:
        raise DomainValidationError(
            "CNAME records must have exactly one value",
            field="values",
        )

    normalized: list[str] = []
    for index, raw in enumerate(values):
        field = f"values[{index}]"
        if not isinstance(raw, str) or not raw.strip():
            raise DomainValidationError("DNS values must be non-empty strings", field=field)
        item = raw.strip()
        if record_type is DnsRecordType.A:
            normalized.append(validate_ipv4_address(item, field=field))
        elif record_type is DnsRecordType.AAAA:
            normalized.append(validate_ipv6_address(item, field=field))
        elif record_type is DnsRecordType.CNAME:
            normalized.append(validate_dns_name(item, field=field))
        else:  # TXT
            if len(item) > 255:
                raise DomainValidationError(
                    "TXT value must be at most 255 characters",
                    field=field,
                )
            normalized.append(item)
    return normalized


def validate_ttl(ttl: int, *, field: str = "ttl_seconds") -> int:
    if not isinstance(ttl, int) or isinstance(ttl, bool):
        raise DomainValidationError(f"{field} must be an integer", field=field)
    if ttl < 60 or ttl > 172800:
        raise DomainValidationError(
            f"{field} must be between 60 and 172800 seconds",
            field=field,
        )
    return ttl


def validate_listener_port(port: int, protocol: ListenerProtocol) -> int:
    validate_port(port, field="listener_port")
    if protocol is ListenerProtocol.HTTP and port == 443:
        raise DomainValidationError(
            "HTTP listeners should not use port 443; use HTTPS",
            field="listener_port",
        )
    if protocol is ListenerProtocol.HTTPS and port == 80:
        raise DomainValidationError(
            "HTTPS listeners should not use port 80; use HTTP",
            field="listener_port",
        )
    return port


def validate_priority(priority: int, *, field: str = "priority") -> int:
    if not isinstance(priority, int) or isinstance(priority, bool):
        raise DomainValidationError(f"{field} must be an integer", field=field)
    if priority < 1 or priority > 50000:
        raise DomainValidationError(
            f"{field} must be between 1 and 50000 inclusive",
            field=field,
        )
    return priority


def validate_certificate_arn(arn: str, *, field: str = "certificate_arn") -> str:
    if not _ACM_CERT_ARN_RE.fullmatch(arn):
        raise DomainValidationError(
            "certificate_arn must be a valid ACM certificate ARN",
            field=field,
        )
    return arn


def validate_security_group_id(sg_id: str, *, field: str = "security_group_id") -> str:
    if not _SG_ID_RE.fullmatch(sg_id):
        raise DomainValidationError(
            "security_group_id must look like sg-xxxxxxxx",
            field=field,
        )
    return sg_id


def validate_listener_arn(arn: str, *, field: str = "listener_arn") -> str:
    if not _LISTENER_ARN_RE.fullmatch(arn):
        raise DomainValidationError(
            "listener_arn must be a valid ELB listener ARN",
            field=field,
        )
    return arn


def validate_sg_protocol_ports(
    protocol: IpProtocol,
    from_port: int | None,
    to_port: int | None,
) -> tuple[int | None, int | None]:
    if protocol is IpProtocol.ALL:
        if from_port is not None or to_port is not None:
            raise DomainValidationError(
                "protocol 'all' must not specify from_port/to_port",
                field="from_port",
            )
        return None, None

    if protocol is IpProtocol.ICMP:
        # ICMP uses type/code in AWS; Switchyard accepts optional type in from_port
        # and code in to_port (0-255), or both omitted for all ICMP.
        if from_port is None and to_port is None:
            return None, None
        if from_port is None or to_port is None:
            raise DomainValidationError(
                "ICMP requires both from_port (type) and to_port (code), or neither",
                field="from_port",
            )
        if not (0 <= from_port <= 255 and 0 <= to_port <= 255):
            raise DomainValidationError(
                "ICMP type/code must be between 0 and 255",
                field="from_port",
            )
        return from_port, to_port

    # TCP / UDP
    if from_port is None or to_port is None:
        raise DomainValidationError(
            f"protocol {protocol.value!r} requires from_port and to_port",
            field="from_port",
        )
    validate_port_range(from_port, to_port)
    return from_port, to_port
