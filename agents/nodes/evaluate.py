import logging

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.models import AuditAction, AuditEntry

logger = logging.getLogger(__name__)

def evaluate_node(state: IncidentState) -> dict:
    """Evaluates the success of the execution (Phase B)."""
    logger.info(f"Running evaluate for incident {state.get('incident_id')}")
    
    if state.get("status") == "REJECTED":
        return {"messages": ["Evaluation skipped because patch was rejected."]}

    audit_logger.record_audit(AuditEntry(
        incident_id=state.get("incident_id"),
        action=AuditAction.EVALUATION_COMPLETED,
        actor="ai-agent",
        details={"status": "RESOLVED"}
    ))
        
    return {"status": "RESOLVED", "messages": ["Evaluation complete (placeholder)"]}
