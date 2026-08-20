import logging

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.models import AuditAction, AuditEntry

logger = logging.getLogger(__name__)

def execute_node(state: IncidentState) -> dict:
    """Executes the approved patch (Phase B)."""
    incident_id = state.get("incident_id")
    logger.info(f"Running execute for incident {incident_id}")
    
    if state.get("status") == "REJECTED":
        return {"messages": ["Execution skipped because patch was rejected."]}

    if incident_id:
        audit_logger.record_audit(AuditEntry(
            incident_id=incident_id,
            action=AuditAction.PATCH_EXECUTED,
            actor="ai-agent"
        ))
        
    return {"messages": ["Execution complete (placeholder)"]}
