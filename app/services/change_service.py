"""Change request application service — orchestration only."""

from __future__ import annotations

from typing import Any

from app.domain.change_request import ChangeRequest
from app.domain.change_spec import ChangeSpecification, deferred_checks_for
from app.domain.enums import ChangeType
from app.domain.errors import DomainValidationError
from app.domain.ids import ChangeSpecId, IdempotencyKey, RequestId
from app.domain.normalize import accept_change_request, parse_inbound, to_domain_change
from app.repositories.base import ChangeRepository
from app.services.errors import IdempotencyConflictError, NotFoundError


class ChangeService:
    """Create and fetch change requests using the Milestone 2 domain layer."""

    def __init__(self, repository: ChangeRepository) -> None:
        self._repository = repository

    def create_change(
        self,
        *,
        actor: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> tuple[ChangeRequest, ChangeSpecification]:
        """Validate via domain, enforce idempotency, persist request+spec.

        `actor` comes from authentication. Payload must not be used to
        impersonate another actor. Persistence stores the normalized
        ChangeSpecification — never arbitrary caller configuration blobs.
        """
        data = dict(payload)
        data.pop("actor", None)
        data["actor"] = actor

        key = self._resolve_idempotency_key(data, idempotency_key)
        if key is not None:
            data["idempotency_key"] = str(key)
        else:
            data.pop("idempotency_key", None)

        # Domain validation first — transport does not reimplement semantics.
        inbound = parse_inbound(data)
        domain_change = to_domain_change(inbound)
        intent_spec_id = self._intent_spec_id(
            environment=inbound.environment,
            change=domain_change,
        )

        if key is not None:
            existing = self._repository.find_by_idempotency(actor, key)
            if existing is not None:
                existing_request, existing_spec = existing
                stored = self._repository.get_idempotency_fingerprint(actor, key)
                if stored != str(intent_spec_id):
                    raise IdempotencyConflictError(
                        "idempotency key was reused with a different change payload",
                        idempotency_key=str(key),
                    )
                return existing_request, existing_spec

        request, specification = accept_change_request(data)
        self._repository.save(request, specification)
        return request, specification

    def get_change(self, request_id: str) -> tuple[ChangeRequest, ChangeSpecification]:
        rid = RequestId.parse(request_id)
        request = self._repository.get_request(rid)
        specification = self._repository.get_specification(rid)
        if request is None or specification is None:
            raise NotFoundError(f"change request not found: {request_id}")
        return request, specification

    def get_request(self, request_id: str) -> ChangeRequest:
        rid = RequestId.parse(request_id)
        request = self._repository.get_request(rid)
        if request is None:
            raise NotFoundError(f"change request not found: {request_id}")
        return request

    @staticmethod
    def _resolve_idempotency_key(
        data: dict[str, Any],
        header_key: str | None,
    ) -> IdempotencyKey | None:
        body_key = data.get("idempotency_key")
        if header_key and body_key and str(body_key) != header_key:
            raise DomainValidationError(
                "Idempotency-Key header and body idempotency_key must match",
                field="idempotency_key",
            )
        raw = header_key or (str(body_key) if body_key is not None else None)
        if raw is None:
            return None
        return IdempotencyKey.parse(raw)

    @staticmethod
    def _intent_spec_id(*, environment: Any, change: Any) -> ChangeSpecId:
        """Content-addressed id for idempotency comparison (no new request id)."""
        change_type = ChangeType(change.change_kind)
        deferred = deferred_checks_for(change_type)
        identity_payload = {
            "schema_version": 1,
            "environment": environment.value,
            "change_type": change_type.value,
            "change": change.model_dump(mode="json"),
            "deferred_checks": [item.value for item in deferred],
        }
        return ChangeSpecId.from_canonical_payload(identity_payload)


__all__ = ["ChangeService"]
