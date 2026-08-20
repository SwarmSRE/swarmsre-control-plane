import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import psycopg

from core.models import AuditEntry

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
SQLITE_PATH = Path(
    os.environ.get("AUDIT_SQLITE_PATH", str(Path(__file__).parent.parent / "data" / "audit.db"))
)


def _serialize_details(details: dict | None) -> str | None:
    """Serialize details dict to JSON string, checking explicitly for None."""
    if details is None:
        return None
    return json.dumps(details)


class _SQLiteBackend:
    """Lightweight SQLite backend for local dev and tests."""

    def __init__(self, db_path: str | Path = SQLITE_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_entries (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incident_id ON audit_entries(incident_id)"
            )

    def record_audit(self, entry: AuditEntry) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO audit_entries (id, incident_id, action, timestamp, actor, details) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    entry.id,
                    entry.incident_id,
                    entry.action.value,
                    entry.timestamp.isoformat(),
                    entry.actor,
                    _serialize_details(entry.details),
                ),
            )

    def _rows_to_entries(self, rows: list[sqlite3.Row]) -> list[AuditEntry]:
        entries = []
        for row in rows:
            entries.append(
                AuditEntry(
                    id=row["id"],
                    incident_id=row["incident_id"],
                    action=row["action"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    actor=row["actor"],
                    details=json.loads(row["details"]) if row["details"] else None,
                )
            )
        return entries

    def get_entries_for_incident(self, incident_id: str) -> list[AuditEntry]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM audit_entries WHERE incident_id = ? ORDER BY timestamp ASC",
                (incident_id,),
            )
            return self._rows_to_entries(cursor.fetchall())

    def get_all_entries(self) -> list[AuditEntry]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM audit_entries ORDER BY timestamp ASC"
            )
            return self._rows_to_entries(cursor.fetchall())


class _PostgreSQLBackend:
    """Production PostgreSQL backend with pgvector-ready schema."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self._init_db()

    def _init_db(self):
        with psycopg.connect(self.dsn) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_entries (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    actor TEXT NOT NULL,
                    details JSONB
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_incident_id
                ON audit_entries(incident_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_entries(timestamp)
                """
            )
            conn.commit()
        logger.info("PostgreSQL audit_entries table initialized.")

    def record_audit(self, entry: AuditEntry) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute(
                "INSERT INTO audit_entries (id, incident_id, action, timestamp, actor, details) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    entry.id,
                    entry.incident_id,
                    entry.action.value,
                    entry.timestamp,
                    entry.actor,
                    _serialize_details(entry.details),
                ),
            )
            conn.commit()

    def _rows_to_entries(self, rows: list[tuple]) -> list[AuditEntry]:
        entries = []
        for row in rows:
            details_raw = row[5]
            if isinstance(details_raw, str):
                details = json.loads(details_raw)
            elif isinstance(details_raw, dict):
                details = details_raw
            else:
                details = None

            entries.append(
                AuditEntry(
                    id=row[0],
                    incident_id=row[1],
                    action=row[2],
                    timestamp=row[3],
                    actor=row[4],
                    details=details,
                )
            )
        return entries

    def get_entries_for_incident(self, incident_id: str) -> list[AuditEntry]:
        with psycopg.connect(self.dsn) as conn:
            cursor = conn.execute(
                "SELECT id, incident_id, action, timestamp, actor, details "
                "FROM audit_entries WHERE incident_id = %s ORDER BY timestamp ASC",
                (incident_id,),
            )
            return self._rows_to_entries(cursor.fetchall())

    def get_all_entries(self) -> list[AuditEntry]:
        with psycopg.connect(self.dsn) as conn:
            cursor = conn.execute(
                "SELECT id, incident_id, action, timestamp, actor, details "
                "FROM audit_entries ORDER BY timestamp ASC"
            )
            return self._rows_to_entries(cursor.fetchall())


class AuditLogger:
    """Unified audit logger that delegates to PostgreSQL or SQLite."""

    def __init__(self, *, database_url: str = "", sqlite_path: str | Path = SQLITE_PATH):
        self._backend: _PostgreSQLBackend | _SQLiteBackend
        if database_url:
            logger.info("Using PostgreSQL backend for audit logging.")
            self._backend = _PostgreSQLBackend(dsn=database_url)
        else:
            logger.info("DATABASE_URL not set — falling back to SQLite for audit logging.")
            self._backend = _SQLiteBackend(db_path=sqlite_path)

    @property
    def db_path(self) -> Path:
        """Expose db_path for SQLite backend (used by tests for cleanup)."""
        if isinstance(self._backend, _SQLiteBackend):
            return self._backend.db_path
        raise AttributeError("db_path is only available on the SQLite backend")

    def record_audit(self, entry: AuditEntry) -> None:
        self._backend.record_audit(entry)
        logger.info(f"Audit recorded: {entry.action.value} for incident {entry.incident_id}")

    def get_entries_for_incident(self, incident_id: str) -> list[AuditEntry]:
        return self._backend.get_entries_for_incident(incident_id)

    def get_all_entries(self) -> list[AuditEntry]:
        return self._backend.get_all_entries()


# Global singleton — uses DATABASE_URL if available, else SQLite
audit_logger = AuditLogger(database_url=DATABASE_URL)
