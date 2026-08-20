import logging

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.models import AuditAction, AuditEntry

logger = logging.getLogger(__name__)

def evaluate_node(state: IncidentState) -> dict:
    """Evaluates the success of the execution (Phase B)."""
    incident_id = state.get("incident_id")
    logger.info(f"Running evaluate for incident {incident_id}")
    
    if state.get("status") == "REJECTED":
        return {"messages": ["Evaluation skipped because patch was rejected."]}

    if incident_id:
        audit_logger.record_audit(AuditEntry(
            incident_id=incident_id,
            action=AuditAction.EVALUATION_COMPLETED,
            actor="ai-agent",
            details={"status": "RESOLVED"}
        ))
        
    return {"status": "RESOLVED", "messages": ["Evaluation complete (placeholder)"]}
