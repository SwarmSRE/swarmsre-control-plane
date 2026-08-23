import logging

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.models import AuditAction, AuditEntry

logger = logging.getLogger(__name__)

def triage_node(state: IncidentState) -> dict:
    """Deterministic 4-signal filter for incident severity."""
    incident_id = state.get("incident_id")
    logger.info(f"Running triage for incident {incident_id}")
    
    event = state.get("raw_event", {})
    reason = event.get("reason", "")
    
    # 4-signal filter + 5 others for robustness
    critical_reasons = {
        "CrashLoopBackOff", "OOMKilled", "FailedCreate", 
        "FailedMount", "FailedScheduling", "BackOff", 
        "Unhealthy", "ImagePullBackOff", "ErrImagePull", "Failed"
    }
    
    msg = (event.get("message") or "").lower()
    is_critical = reason in critical_reasons or any(k in msg for k in ["imagepullbackoff", "errimagepull", "crashloopbackoff", "oomkilled", "failed"])

    if is_critical:
        if incident_id:
            audit_logger.record_audit(AuditEntry(
                incident_id=incident_id,
                action=AuditAction.TRIAGE_COMPLETED,
                actor="ai-agent",
                details={"triage_result": "passed", "reason": reason}
            ))
        return {"status": "INVESTIGATING", "messages": [f"Triage passed: {reason}"]}

    if incident_id:
        audit_logger.record_audit(AuditEntry(
            incident_id=incident_id,
            action=AuditAction.TRIAGE_COMPLETED,
            actor="ai-agent",
            details={"triage_result": "filtered", "reason": reason}
        ))
    return {"status": "RESOLVED", "messages": [f"Triage filtered out: {reason}"]}
