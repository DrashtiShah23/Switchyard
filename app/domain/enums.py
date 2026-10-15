"""Enumerations that close the domain's valid state space."""

from __future__ import annotations

from enum import StrEnum


class Environment(StrEnum):
    """Known deployment environments. Unknown values are rejected."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class ChangeType(StrEnum):
    """Supported network change capabilities."""

    DNS_RECORD = "dns_record"
    LOAD_BALANCER_ROUTE = "load_balancer_route"
    TLS_BINDING = "tls_binding"
    SECURITY_GROUP_RULE = "security_group_rule"


class DesiredAction(StrEnum):
    """Intent against an existing or new managed resource."""

    CREATE = "create"
    UPDATE = "update"


class LifecycleState(StrEnum):
    """Explicit change-request lifecycle states."""

    REQUESTED = "requested"
    VALIDATED = "validated"
    PLANNED = "planned"
    POLICY_REJECTED = "policy_rejected"
    AWAITING_APPROVAL = "awaiting_approval"
    APPLYING = "applying"
    VERIFYING = "verifying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class LifecycleEvent(StrEnum):
    """Events that drive the lifecycle state machine."""

    VALIDATION_SUCCEEDED = "validation_succeeded"
    VALIDATION_FAILED = "validation_failed"
    PLAN_SUCCEEDED = "plan_succeeded"
    PLAN_FAILED = "plan_failed"
    POLICY_PASSED = "policy_passed"
    POLICY_REJECTED = "policy_rejected"
    POLICY_ENGINE_FAILED = "policy_engine_failed"
    APPLY_STARTED = "apply_started"
    APPLY_SUCCEEDED = "apply_succeeded"
    APPLY_FAILED = "apply_failed"
    VERIFICATION_SUCCEEDED = "verification_succeeded"
    VERIFICATION_FAILED = "verification_failed"
    ABANDONED = "abandoned"


class DnsRecordType(StrEnum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    TXT = "TXT"


class IpProtocol(StrEnum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ALL = "all"


class TrafficDirection(StrEnum):
    INGRESS = "ingress"
    EGRESS = "egress"


class ListenerProtocol(StrEnum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    TCP = "TCP"
    TLS = "TLS"


class RouteActionType(StrEnum):
    """ALB actions Switchyard supports as product abstractions."""

    FIXED_RESPONSE = "fixed_response"
    FORWARD = "forward"


class DeferredInventoryCheck(StrEnum):
    """Checks that require authoritative live infrastructure state.

    The domain does not perform these. They are declared on the normalized
    change specification so later stages (policy fixtures / AWS reconciliation)
    can own them explicitly.
    """

    DNS_DUPLICATE_OWNERSHIP = "dns_duplicate_ownership"
    CIDR_OVERLAP_WITH_LIVE_SG = "cidr_overlap_with_live_sg"
    CERTIFICATE_EXISTS = "certificate_exists"
    LISTENER_EXISTS = "listener_exists"
    SECURITY_GROUP_EXISTS = "security_group_exists"
    HOSTED_ZONE_EXISTS = "hosted_zone_exists"
