"""SQLite implementation of ChangeRepository (local zero-cost persistence)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.domain.change_request import ChangeRequest
from app.domain.change_spec import ChangeSpecification
from app.domain.ids import IdempotencyKey, RequestId


class SqliteChangeRepository:
    """Stores domain aggregates as JSON documents behind the repository port."""

    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        # Keep a dedicated connection for in-memory DBs so schema persists.
        self._memory_conn: sqlite3.Connection | None = None
        if database_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self._database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS change_requests (
                    request_id TEXT PRIMARY KEY,
                    actor TEXT NOT NULL,
                    idempotency_key TEXT,
                    fingerprint TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS ux_change_requests_actor_idem
                    ON change_requests(actor, idempotency_key)
                    WHERE idempotency_key IS NOT NULL;

                CREATE TABLE IF NOT EXISTS change_specifications (
                    request_id TEXT PRIMARY KEY,
                    change_spec_id TEXT NOT NULL,
                    spec_json TEXT NOT NULL,
                    FOREIGN KEY(request_id) REFERENCES change_requests(request_id)
                );
                """
            )
            conn.commit()
        finally:
            if self._memory_conn is None:
                conn.close()

    def save(self, request: ChangeRequest, specification: ChangeSpecification) -> None:
        if specification.request_id != request.request_id:
            raise ValueError("specification.request_id must match request.request_id")
        fingerprint = self._fingerprint_from_spec(specification)
        conn = self._connect()
        try:
            conn.execute("BEGIN")
            conn.execute(
                """
                INSERT INTO change_requests (
                    request_id, actor, idempotency_key, fingerprint,
                    request_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(request.request_id),
                    request.actor,
                    str(request.idempotency_key) if request.idempotency_key else None,
                    fingerprint,
                    json.dumps(request.to_dict(), sort_keys=True),
                    request.to_dict()["created_at"],
                    request.to_dict()["updated_at"],
                ),
            )
            conn.execute(
                """
                INSERT INTO change_specifications (
                    request_id, change_spec_id, spec_json
                ) VALUES (?, ?, ?)
                """,
                (
                    str(request.request_id),
                    str(specification.change_spec_id),
                    json.dumps(specification.to_dict(), sort_keys=True),
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if self._memory_conn is None:
                conn.close()

    def get_request(self, request_id: RequestId) -> ChangeRequest | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT request_json FROM change_requests WHERE request_id = ?",
                (str(request_id),),
            ).fetchone()
        finally:
            if self._memory_conn is None:
                conn.close()
        if row is None:
            return None
        return ChangeRequest.from_dict(json.loads(row["request_json"]))

    def get_specification(self, request_id: RequestId) -> ChangeSpecification | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT spec_json FROM change_specifications WHERE request_id = ?",
                (str(request_id),),
            ).fetchone()
        finally:
            if self._memory_conn is None:
                conn.close()
        if row is None:
            return None
        return ChangeSpecification.from_dict(json.loads(row["spec_json"]))

    def find_by_idempotency(
        self,
        actor: str,
        idempotency_key: IdempotencyKey,
    ) -> tuple[ChangeRequest, ChangeSpecification] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT r.request_json, s.spec_json
                FROM change_requests r
                JOIN change_specifications s ON s.request_id = r.request_id
                WHERE r.actor = ? AND r.idempotency_key = ?
                """,
                (actor, str(idempotency_key)),
            ).fetchone()
        finally:
            if self._memory_conn is None:
                conn.close()
        if row is None:
            return None
        request = ChangeRequest.from_dict(json.loads(row["request_json"]))
        spec = ChangeSpecification.from_dict(json.loads(row["spec_json"]))
        return request, spec

    def get_idempotency_fingerprint(
        self,
        actor: str,
        idempotency_key: IdempotencyKey,
    ) -> str | None:
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT fingerprint FROM change_requests
                WHERE actor = ? AND idempotency_key = ?
                """,
                (actor, str(idempotency_key)),
            ).fetchone()
        finally:
            if self._memory_conn is None:
                conn.close()
        if row is None:
            return None
        return str(row["fingerprint"])

    @staticmethod
    def _fingerprint_from_spec(specification: ChangeSpecification) -> str:
        # Fingerprint intent from the normalized specification identity.
        return str(specification.change_spec_id)
