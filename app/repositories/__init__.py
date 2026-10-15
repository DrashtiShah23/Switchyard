"""Persistence interfaces and implementations (SQLite for local demo)."""

from app.repositories.sqlite import SqliteChangeRepository

__all__ = ["SqliteChangeRepository"]
