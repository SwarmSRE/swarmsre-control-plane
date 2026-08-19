import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from core.models import AuditEntry

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "audit.db"

class AuditLogger:
    def __init__(self, db_path: str | Path = DB_PATH):
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
            # Create an index for faster queries by incident
            conn.execute("CREATE INDEX IF NOT EXISTS idx_incident_id ON audit_entries(incident_id)")

    def record_audit(self, entry: AuditEntry) -> None:
        """Records an audit entry into the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_entries (id, incident_id, action, timestamp, actor, details)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.incident_id,
                    entry.action.value,
                    entry.timestamp.isoformat(),
                    entry.actor,
                    json.dumps(entry.details) if entry.details else None,
                ),
            )
        logger.info(f"Audit recorded: {entry.action.value} for incident {entry.incident_id}")

    def get_entries_for_incident(self, incident_id: str) -> list[AuditEntry]:
        """Retrieves all audit entries for a given incident."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM audit_entries WHERE incident_id = ? ORDER BY timestamp ASC",
                (incident_id,)
            )
            rows = cursor.fetchall()
            
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

    def get_all_entries(self) -> list[AuditEntry]:
        """Retrieves all audit entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM audit_entries ORDER BY timestamp ASC")
            rows = cursor.fetchall()
            
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

# Global singleton
audit_logger = AuditLogger()
