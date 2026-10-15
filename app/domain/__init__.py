"""Switchyard domain layer.

Pure models, validation, normalization, and lifecycle transitions.
No FastAPI routes, SQLite, Terraform, OPA, AWS SDK, or subprocess usage.
"""

from app.domain.change_request import ChangeRequest
from app.domain.change_spec import ChangeSpecification
from app.domain.changes import (
    DnsRecordChange,
    FixedResponseAction,
    ForwardAction,
    LoadBalancerRouteChange,
    SecurityGroupRuleChange,
    TlsBindingChange,
)
from app.domain.enums import (
    ChangeType,
    DeferredInventoryCheck,
    DesiredAction,
    DnsRecordType,
    Environment,
    IpProtocol,
    LifecycleEvent,
    LifecycleState,
    ListenerProtocol,
    RouteActionType,
    TrafficDirection,
)
from app.domain.errors import DomainError, DomainValidationError, IllegalTransitionError
from app.domain.ids import ChangeSpecId, IdempotencyKey, RequestId
from app.domain.inbound import InboundChangeRequest
from app.domain.lifecycle import (
    all_legal_transitions,
    allowed_events,
    can_transition,
    is_terminal,
    transition,
)
from app.domain.normalize import accept_change_request, parse_inbound, to_domain_change

__all__ = [
    "ChangeRequest",
    "ChangeSpecId",
    "ChangeSpecification",
    "ChangeType",
    "DeferredInventoryCheck",
    "DesiredAction",
    "DnsRecordChange",
    "DnsRecordType",
    "DomainError",
    "DomainValidationError",
    "Environment",
    "FixedResponseAction",
    "ForwardAction",
    "IdempotencyKey",
    "IllegalTransitionError",
    "InboundChangeRequest",
    "IpProtocol",
    "LifecycleEvent",
    "LifecycleState",
    "ListenerProtocol",
    "LoadBalancerRouteChange",
    "RequestId",
    "RouteActionType",
    "SecurityGroupRuleChange",
    "TlsBindingChange",
    "TrafficDirection",
    "accept_change_request",
    "all_legal_transitions",
    "allowed_events",
    "can_transition",
    "is_terminal",
    "parse_inbound",
    "to_domain_change",
    "transition",
]
