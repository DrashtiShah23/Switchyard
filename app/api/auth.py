"""Demo authentication types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedActor:
    """Caller identity derived from a configured demo API key."""

    actor: str
    api_key_id: str
