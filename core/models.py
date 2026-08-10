from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

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
    raw_event: Optional[Dict[str, Any]] = None

class IncidentResponse(BaseModel):
    id: str
    title: str
    description: str
    status: IncidentStatus
    source: str
    created_at: datetime
    updated_at: datetime
    raw_event: Optional[Dict[str, Any]] = None
    rca_summary: Optional[str] = None
    proposed_patch: Optional[str] = None

class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    status: IncidentStatus = IncidentStatus.OPEN
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    raw_event: Optional[Dict[str, Any]] = None
    rca_summary: Optional[str] = None
    proposed_patch: Optional[str] = None
