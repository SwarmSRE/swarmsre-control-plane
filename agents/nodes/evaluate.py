import json
import logging

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.mcp_client import mcp
from core.models import AuditAction, AuditEntry

logger = logging.getLogger(__name__)

async def evaluate_node(state: IncidentState) -> dict:
    """Evaluates the success of the execution via MCP."""
    incident_id = state.get("incident_id")
    logger.info(f"Running evaluate for incident {incident_id}")
    
    if state.get("status") == "REJECTED":
        return {"messages": ["Evaluation skipped because patch was rejected."]}

    # Fetch pod status based on the raw_event
    raw_event = state.get("raw_event", {})
    # Support both snake_case (from watcher) and camelCase (from manual creation)
    involved_object = raw_event.get("involved_object") or raw_event.get("involvedObject", {})
    pod_name = involved_object.get("name", "")
    namespace = involved_object.get("namespace") or raw_event.get("namespace", "default")
    
    if not pod_name:
        logger.warning(f"Evaluate for {incident_id}: no pod name in raw_event, skipping live check")
        return {
            "status": "PROPOSED",
            "messages": [f"[Evaluator] Skipped live pod check — no pod name in event data. Deferring to human review."]
        }
    
    try:
        status_json = await mcp.fetch_pod_status(namespace, pod_name)
        status_data = json.loads(status_json)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Evaluate for {incident_id}: could not fetch pod status: {e}")
        return {
            "status": "PROPOSED",
            "messages": [f"[Evaluator] Could not fetch live pod status for {namespace}/{pod_name}: {e}. Deferring to human review."]
        }
    
    # Simple evaluation heuristics: Phase must be Running or Succeeded
    phase = status_data.get("status", {}).get("phase", "")
    
    if phase in ["Running", "Succeeded"]:
        success = True
        eval_details = {"phase": phase, "status": "RESOLVED"}
    else:
        success = False
        eval_details = {"phase": phase, "status": "INVESTIGATING (Retrying)"}
        
    final_status = "RESOLVED" if success else "INVESTIGATING"

    if incident_id:
        audit_logger.record_audit(AuditEntry(
            incident_id=incident_id,
            action=AuditAction.EVALUATION_COMPLETED,
            actor="ai-agent",
            details=eval_details
        ))
        
    return {
        "status": final_status, 
        "messages": [f"[Evaluator] Evaluation complete. Pod phase: {phase}. Success: {success}"]
    }

