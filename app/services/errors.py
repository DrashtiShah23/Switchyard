"""Application-service errors (not HTTP, not domain)."""

from __future__ import annotations


class ServiceError(Exception):
    """Base application service error."""


class NotFoundError(ServiceError):
    """Requested aggregate does not exist."""


class IdempotencyConflictError(ServiceError):
    """Idempotency key reused with a different change payload."""

    def __init__(self, message: str, *, idempotency_key: str) -> None:
        self.idempotency_key = idempotency_key
        super().__init__(message)


class UnauthorizedError(ServiceError):
    """Caller authentication failed."""
