"""Application configuration from environment (no secrets committed)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _parse_api_keys(raw: str) -> dict[str, str]:
    """Parse `key:actor,key2:actor2` into a mapping."""
    mapping: dict[str, str] = {}
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(
                "SWITCHYARD_API_KEYS entries must be api_key:actor pairs",
            )
        key, actor = item.split(":", 1)
        key = key.strip()
        actor = actor.strip()
        if not key or not actor:
            raise ValueError("SWITCHYARD_API_KEYS entries must be non-empty api_key:actor")
        mapping[key] = actor
    return mapping


@dataclass(frozen=True)
class Settings:
    env_name: str
    database_url: str
    api_keys: dict[str, str]
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            env_name=os.getenv("SWITCHYARD_ENV", "local"),
            database_url=os.getenv(
                "SWITCHYARD_DATABASE_URL",
                "sqlite:///./data/switchyard.db",
            ),
            api_keys=_parse_api_keys(
                os.getenv("SWITCHYARD_API_KEYS", "replace-me:local-developer")
            ),
            log_level=os.getenv("SWITCHYARD_LOG_LEVEL", "INFO"),
        )


def sqlite_path_from_url(database_url: str) -> str:
    """Extract a filesystem path from a sqlite URL."""
    if database_url in {"sqlite:///:memory:", "sqlite://"}:
        return ":memory:"
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError(
            "only sqlite:/// URLs are supported for local persistence",
        )
    path = database_url[len(prefix) :]
    if path == ":memory:":
        return ":memory:"
    return path
