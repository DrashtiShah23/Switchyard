"""Persistence abstractions — domain types in, no SQL/HTTP leakage out."""

from __future__ import annotations

from typing import Protocol

from app.domain.change_request import ChangeRequest
from app.domain.change_spec import ChangeSpecification
from app.domain.ids import IdempotencyKey, RequestId


class ChangeRepository(Protocol):
    """Port for durable change requests and normalized specifications."""

    def save(self, request: ChangeRequest, specification: ChangeSpecification) -> None:
        """Persist a request and its normalized change specification atomically."""

    def get_request(self, request_id: RequestId) -> ChangeRequest | None:
        """Load a change request by id."""

    def get_specification(self, request_id: RequestId) -> ChangeSpecification | None:
        """Load the normalized specification for a request."""

    def find_by_idempotency(
        self,
        actor: str,
        idempotency_key: IdempotencyKey,
    ) -> tuple[ChangeRequest, ChangeSpecification] | None:
        """Return the prior request+spec for an actor/idempotency key pair."""

    def get_idempotency_fingerprint(
        self,
        actor: str,
        idempotency_key: IdempotencyKey,
    ) -> str | None:
        """Return the stored request fingerprint for conflict detection."""
