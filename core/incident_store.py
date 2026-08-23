import json
import logging
import os
from typing import Any

import psycopg

from core.models import Incident, IncidentStatus

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _serialize_json(data: Any) -> str | None:
    if data is None:
        return None
    return json.dumps(data)


def _deserialize_json(data_raw: Any) -> Any:
    if isinstance(data_raw, str):
        return json.loads(data_raw)
    return data_raw


class _PostgreSQLIncidentBackend:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._init_db()

    def _init_db(self):
        with psycopg.connect(self.dsn) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL,
                    raw_event JSONB,
                    rca_summary TEXT,
                    proposed_patch TEXT,
                    confidence_score FLOAT,
                    evidence_chain JSONB,
                    log_hunter_output JSONB,
                    telemetry_output JSONB,
                    gitops_output JSONB,
                    agent_trace JSONB
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_incidents_status
                ON incidents(status)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_incidents_created_at
                ON incidents(created_at DESC)
                """
            )
            # CNCF-Grade Migration: Ensure new columns exist for existing deployments
            try:
                conn.execute("ALTER TABLE incidents ADD COLUMN IF NOT EXISTS gitops_output JSONB")
            except psycopg.errors.DuplicateColumn:
                pass
            conn.commit()
        logger.info("PostgreSQL incidents table initialized.")

    def save(self, incident: Incident) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute(
                """
                INSERT INTO incidents (
                    id, title, description, status, source, created_at, updated_at,
                    raw_event, rca_summary, proposed_patch, confidence_score,
                    evidence_chain, log_hunter_output, telemetry_output, gitops_output, agent_trace
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status,
                    source = EXCLUDED.source,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at,
                    raw_event = EXCLUDED.raw_event,
                    rca_summary = EXCLUDED.rca_summary,
                    proposed_patch = EXCLUDED.proposed_patch,
                    confidence_score = EXCLUDED.confidence_score,
                    evidence_chain = EXCLUDED.evidence_chain,
                    log_hunter_output = EXCLUDED.log_hunter_output,
                    telemetry_output = EXCLUDED.telemetry_output,
                    gitops_output = EXCLUDED.gitops_output,
                    agent_trace = EXCLUDED.agent_trace
                """,
                (
                    incident.id,
                    incident.title,
                    incident.description,
                    incident.status.value,
                    incident.source,
                    incident.created_at,
                    incident.updated_at,
                    _serialize_json(incident.raw_event),
                    incident.rca_summary,
                    incident.proposed_patch,
                    incident.confidence_score,
                    _serialize_json(incident.evidence_chain),
                    _serialize_json(incident.log_hunter_output),
                    _serialize_json(incident.telemetry_output),
                    _serialize_json(incident.gitops_output),
                    _serialize_json(incident.agent_trace),
                ),
            )
            conn.commit()

    def _row_to_incident(self, row: tuple) -> Incident:
        return Incident(
            id=row[0],
            title=row[1],
            description=row[2],
            status=IncidentStatus(row[3]),
            source=row[4],
            created_at=row[5],
            updated_at=row[6],
            raw_event=_deserialize_json(row[7]),
            rca_summary=row[8],
            proposed_patch=row[9],
            confidence_score=row[10],
            evidence_chain=_deserialize_json(row[11]) or [],
            log_hunter_output=_deserialize_json(row[12]),
            telemetry_output=_deserialize_json(row[13]),
            gitops_output=_deserialize_json(row[14]),
            agent_trace=_deserialize_json(row[15]) or [],
        )

    def get(self, incident_id: str) -> Incident | None:
        with psycopg.connect(self.dsn) as conn:
            cursor = conn.execute(
                """
                SELECT id, title, description, status, source, created_at, updated_at,
                       raw_event, rca_summary, proposed_patch, confidence_score,
                       evidence_chain, log_hunter_output, telemetry_output, gitops_output, agent_trace
                FROM incidents WHERE id = %s
                """,
                (incident_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_incident(row)

    def list_all(self) -> list[Incident]:
        with psycopg.connect(self.dsn) as conn:
            cursor = conn.execute(
                """
                SELECT id, title, description, status, source, created_at, updated_at,
                       raw_event, rca_summary, proposed_patch, confidence_score,
                       evidence_chain, log_hunter_output, telemetry_output, gitops_output, agent_trace
                FROM incidents ORDER BY created_at DESC
                """
            )
            return [self._row_to_incident(row) for row in cursor.fetchall()]


class IncidentStore:
    """Incident store backed by PostgreSQL."""

    def __init__(self, *, database_url: str):
        self._database_url = database_url
        self._backend: _PostgreSQLIncidentBackend | None = None

    def _get_backend(self) -> _PostgreSQLIncidentBackend:
        if self._backend is None:
            if not self._database_url:
                raise ValueError("DATABASE_URL is required.")
            logger.info("Using PostgreSQL backend for incidents.")
            self._backend = _PostgreSQLIncidentBackend(dsn=self._database_url)
        return self._backend

    def save(self, incident: Incident) -> None:
        self._get_backend().save(incident)

    def get(self, incident_id: str) -> Incident | None:
        return self._get_backend().get(incident_id)

    def list_all(self) -> list[Incident]:
        return self._get_backend().list_all()


# Global singleton
incident_store = IncidentStore(database_url=DATABASE_URL)
