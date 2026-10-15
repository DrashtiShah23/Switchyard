"""Domain-layer error types."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for domain failures."""


class DomainValidationError(DomainError, ValueError):
    """Input failed domain validation (network semantics or invariants).

    Also subclasses ValueError so Pydantic validators preserve the message.
    """

    def __init__(self, message: str, *, field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


class IllegalTransitionError(DomainError):
    """A lifecycle transition is not permitted from the current state."""

    def __init__(
        self,
        message: str,
        *,
        current_state: str,
        event: str,
    ) -> None:
        self.current_state = current_state
        self.event = event
        super().__init__(message)
