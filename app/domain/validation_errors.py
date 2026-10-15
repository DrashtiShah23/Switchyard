"""Helpers to surface DomainValidationError through Pydantic wrappers."""

from __future__ import annotations

from pydantic import ValidationError

from app.domain.errors import DomainValidationError


def unwrap_domain_validation_error(exc: BaseException) -> DomainValidationError | None:
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, DomainValidationError):
            return current
        if isinstance(current, ValidationError):
            for err in current.errors():
                ctx = err.get("ctx") or {}
                nested = ctx.get("error")
                if isinstance(nested, DomainValidationError):
                    return nested
                if isinstance(nested, Exception):
                    found = unwrap_domain_validation_error(nested)
                    if found is not None:
                        return found
        current = current.__cause__ or current.__context__
    return None


def raise_as_domain_validation(exc: ValidationError) -> None:
    found = unwrap_domain_validation_error(exc)
    if found is not None:
        raise found from exc
    parts: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(item) for item in err.get("loc", ()))
        msg = err.get("msg", "invalid")
        parts.append(f"{loc}: {msg}" if loc else msg)
    message = "; ".join(parts) if parts else "invalid request"
    raise DomainValidationError(message) from exc
