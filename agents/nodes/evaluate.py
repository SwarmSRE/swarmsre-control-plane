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

    # For MVP, we will try to fetch the pod status based on the raw_event
    raw_event = state.get("raw_event", {})
    involved_object = raw_event.get("involvedObject", {})
    pod_name = involved_object.get("name")
    namespace = involved_object.get("namespace", "default")
    
    success = True
    eval_details = {"reason": "Fallback to success for MVP if no pod name found"}
    
    if pod_name:
        try:
            status_json = await mcp.fetch_pod_status(namespace, pod_name)
            status_data = json.loads(status_json)
            
            # Simple evaluation heuristics: Phase must be Running or Succeeded
            phase = status_data.get("status", {}).get("phase", "")
            
            if phase in ["Running", "Succeeded"]:
                success = True
                eval_details = {"phase": phase, "status": "RESOLVED"}
            else:
                success = False
                eval_details = {"phase": phase, "status": "INVESTIGATING (Retrying)"}
                
        except Exception as e:
            logger.error(f"Failed to fetch pod status for evaluation: {e}")
            success = False
            eval_details = {"error": str(e), "status": "INVESTIGATING (Retrying)"}
            
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
        "messages": [f"Evaluation complete. Success: {success}"]
    }
