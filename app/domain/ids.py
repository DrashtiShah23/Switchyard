"""Stable identifiers for requests and change specifications."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Self

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from app.domain.errors import DomainValidationError

_REQUEST_ID_RE = re.compile(r"^req_[0-9a-f]{32}$")
_SPEC_ID_RE = re.compile(r"^spec_[0-9a-f]{32}$")
_IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class RequestId(str):
    """Opaque, stable request identifier (`req_` + 32 hex chars)."""

    __slots__ = ()

    @classmethod
    def generate(cls) -> Self:
        return cls(f"req_{uuid.uuid4().hex}")

    @classmethod
    def parse(cls, value: str) -> Self:
        if not _REQUEST_ID_RE.fullmatch(value):
            raise DomainValidationError(
                f"invalid request id format: {value!r}",
                field="request_id",
            )
        return cls(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.parse)


class ChangeSpecId(str):
    """Content-addressed change specification id (`spec_` + 32 hex chars).

    Derived from the canonical normalized payload so identical intents share an
    identity useful for auditing and future idempotent comparison.
    """

    __slots__ = ()

    @classmethod
    def from_canonical_payload(cls, payload: dict[str, Any]) -> Self:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:32]
        return cls(f"spec_{digest}")

    @classmethod
    def parse(cls, value: str) -> Self:
        if not _SPEC_ID_RE.fullmatch(value):
            raise DomainValidationError(
                f"invalid change specification id format: {value!r}",
                field="change_spec_id",
            )
        return cls(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.parse)


class IdempotencyKey(str):
    """Caller-supplied idempotency key.

    Stored on the domain request so Milestone 3 can bind HTTP idempotency
    without reshaping the domain model. This milestone does not implement the
    HTTP mechanism.
    """

    __slots__ = ()

    @classmethod
    def parse(cls, value: str) -> Self:
        if not _IDEMPOTENCY_KEY_RE.fullmatch(value):
            raise DomainValidationError(
                "idempotency key must be 1-128 chars of [A-Za-z0-9._:-]",
                field="idempotency_key",
            )
        return cls(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.parse)
