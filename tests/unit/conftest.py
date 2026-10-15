"""Shared fixtures for domain unit tests."""

from __future__ import annotations

from typing import Any


def dns_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "environment": "dev",
        "actor": "alice",
        "change": {
            "change_type": "dns_record",
            "action": "create",
            "name": "app.example.com",
            "record_type": "A",
            "values": ["1.2.3.4"],
            "ttl_seconds": 300,
        },
    }
    change_overrides = overrides.pop("change", {})
    base.update(overrides)
    base["change"] = {**base["change"], **change_overrides}
    return base


def lb_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "environment": "dev",
        "actor": "alice",
        "change": {
            "change_type": "load_balancer_route",
            "action": "create",
            "load_balancer_name": "app-alb",
            "listener_port": 80,
            "listener_protocol": "HTTP",
            "priority": 100,
            "path_pattern": "/health",
            "route_action": {
                "action_type": "fixed_response",
                "status_code": 200,
                "message_body": "ok",
            },
        },
    }
    change_overrides = overrides.pop("change", {})
    base.update(overrides)
    base["change"] = {**base["change"], **change_overrides}
    return base


def tls_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "environment": "staging",
        "actor": "alice",
        "change": {
            "change_type": "tls_binding",
            "action": "update",
            "listener_arn": (
                "arn:aws:elasticloadbalancing:us-west-2:123456789012:"
                "listener/app/my-alb/50dc6c495c0c9188/f2f7dc8efc522ab2"
            ),
            "certificate_arn": (
                "arn:aws:acm:us-west-2:123456789012:certificate/"
                "12345678-1234-1234-1234-123456789012"
            ),
            "default_certificate": True,
        },
    }
    change_overrides = overrides.pop("change", {})
    base.update(overrides)
    base["change"] = {**base["change"], **change_overrides}
    return base


def sg_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "environment": "prod",
        "actor": "alice",
        "change": {
            "change_type": "security_group_rule",
            "action": "create",
            "security_group_id": "sg-0123456789abcdef0",
            "direction": "ingress",
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["10.0.0.0/8"],
            "description": "allow https from corp",
        },
    }
    change_overrides = overrides.pop("change", {})
    base.update(overrides)
    base["change"] = {**base["change"], **change_overrides}
    return base
