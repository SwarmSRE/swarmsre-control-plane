import asyncio
import json
import logging

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.mcp_client import mcp
from core.models import AuditAction, AuditEntry

logger = logging.getLogger(__name__)

async def quarantine_node(state: IncidentState) -> dict:
    """Quarantines a failing pod to isolate it from traffic for forensic investigation."""
    incident_id = state.get("incident_id")
    logger.info(f"Running quarantine for incident {incident_id}")
    
    event = state.get("raw_event", {})
    involved = event.get("involved_object", {})
    
    namespace = involved.get("namespace", "default")
    pod_name = involved.get("name", "")
    
    if not pod_name:
        logger.warning(f"Quarantine skipped for {incident_id}: no pod name in raw_event")
        return {"status": "INVESTIGATING", "messages": ["[Quarantine] Skipped: No pod name found in event."]}

    # Execute quarantine via MCP
    result_str = await mcp.quarantine_pod(namespace, pod_name, incident_id or "unknown")
    
    try:
        result = json.loads(result_str)
    except Exception:
        result = {"success": False, "error": result_str}
        
    if result.get("success"):
        if incident_id:
            await asyncio.to_thread(
                audit_logger.record_audit,
                AuditEntry(
                    incident_id=incident_id,
                    action=AuditAction.POD_QUARANTINED,
                    actor="ai-agent",
                    details=result,
                ),
            )
        msg = f"[Quarantine] Successfully isolated pod {namespace}/{pod_name}. Original app label: {result.get('original_app_label')}"
        return {
            "status": "QUARANTINED",
            "quarantine_result": result,
            "messages": [msg]
        }
    else:
        # If quarantine fails, we just log it and proceed to investigation anyway
        msg = f"[Quarantine] Failed to quarantine pod {namespace}/{pod_name}: {result.get('error')}"
        logger.warning(msg)
        return {
            "status": "INVESTIGATING",
            "messages": [msg]
        }
