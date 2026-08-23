import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    PROPOSED = "PROPOSED"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"

class IncidentCreate(BaseModel):
    title: str
    description: str
    source: str = "kubernetes-watcher"
    raw_event: dict[str, Any] | None = None

class PatchProposal(BaseModel):
    incident_id: str
    patch_yaml: str
    reasoning: str

class IncidentResponse(BaseModel):
    id: str
    title: str
    description: str
    status: IncidentStatus
    source: str
    created_at: datetime
    updated_at: datetime
    raw_event: dict[str, Any] | None = None
    rca_summary: str | None = None
    proposed_patch: str | None = None
    confidence_score: float | None = None
    evidence_chain: list[dict[str, Any]] = Field(default_factory=list)
    log_hunter_output: dict[str, Any] | None = None
    telemetry_output: dict[str, Any] | None = None
    agent_trace: list[dict[str, Any]] = Field(default_factory=list)

class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    status: IncidentStatus = IncidentStatus.OPEN
    source: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_event: dict[str, Any] | None = None
    rca_summary: str | None = None
    proposed_patch: str | None = None
    confidence_score: float | None = None
    evidence_chain: list[dict[str, Any]] = Field(default_factory=list)
    log_hunter_output: dict[str, Any] | None = None
    telemetry_output: dict[str, Any] | None = None
    agent_trace: list[dict[str, Any]] = Field(default_factory=list)

class AuditAction(str, Enum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    TRIAGE_COMPLETED = "TRIAGE_COMPLETED"
    INVESTIGATION_COMPLETED = "INVESTIGATION_COMPLETED"
    PATCH_PROPOSED = "PATCH_PROPOSED"
    PATCH_APPROVED = "PATCH_APPROVED"
    PATCH_REJECTED = "PATCH_REJECTED"
    PATCH_EXECUTED = "PATCH_EXECUTED"
    EVALUATION_COMPLETED = "EVALUATION_COMPLETED"

class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    action: AuditAction
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    actor: str = "system"  # e.g., "ai-agent", "human-approver", "system"
    details: dict[str, Any] | None = None

