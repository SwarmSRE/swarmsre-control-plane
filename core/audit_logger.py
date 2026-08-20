import json
import logging
import os

import psycopg

from core.models import AuditEntry

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _serialize_details(details: dict | None) -> str | None:
    """Serialize details dict to JSON string, checking explicitly for None."""
    if details is None:
        return None
    return json.dumps(details)


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
    """Audit logger backed by PostgreSQL."""

    def __init__(self, *, database_url: str):
        self._database_url = database_url
        self._backend: _PostgreSQLBackend | None = None

    def _get_backend(self) -> _PostgreSQLBackend:
        if self._backend is None:
            if not self._database_url:
                raise ValueError(
                    "DATABASE_URL is required. Set it in your environment or .env file. "
                    "Example: DATABASE_URL=postgresql://swarmsre:swarmsre-dev@localhost:5432/swarmsre"
                )
            logger.info("Using PostgreSQL backend for audit logging.")
            self._backend = _PostgreSQLBackend(dsn=self._database_url)
        return self._backend

    def record_audit(self, entry: AuditEntry) -> None:
        self._get_backend().record_audit(entry)
        logger.info(f"Audit recorded: {entry.action.value} for incident {entry.incident_id}")

    def get_entries_for_incident(self, incident_id: str) -> list[AuditEntry]:
        return self._get_backend().get_entries_for_incident(incident_id)

    def get_all_entries(self) -> list[AuditEntry]:
        return self._get_backend().get_all_entries()


# Global singleton — PostgreSQL only (lazy-initialized on first use)
audit_logger = AuditLogger(database_url=DATABASE_URL)

