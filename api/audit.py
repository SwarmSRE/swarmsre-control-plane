from fastapi import APIRouter

from core.audit_logger import audit_logger
from core.models import AuditEntry

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/{incident_id}", response_model=list[AuditEntry])
def get_incident_audit_trail(incident_id: str):
    """Retrieves the complete audit trail for a specific incident."""
    return audit_logger.get_entries_for_incident(incident_id)

@router.get("/", response_model=list[AuditEntry])
def get_all_audits():
    """Retrieves all audit entries across the system."""
    return audit_logger.get_all_entries()
