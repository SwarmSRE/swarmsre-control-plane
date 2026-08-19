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
