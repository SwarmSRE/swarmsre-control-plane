import asyncio
import logging

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.mcp_client import mcp
from core.models import AuditAction, AuditEntry

logger = logging.getLogger(__name__)

async def investigate_node(state: IncidentState) -> dict:
    """Fetches pod logs and events using the MCP client."""
    incident_id = state.get("incident_id")
    logger.info(f"Running investigation for incident {incident_id}")
    
    event = state.get("raw_event", {})
    involved = event.get("involved_object", {})
    
    namespace = involved.get("namespace", "default")
    pod_name = involved.get("name", "")
    
    if not pod_name:
        raise ValueError(f"Investigation failed for {incident_id}: no pod name in raw_event")
        
    logs = await mcp.fetch_pod_logs(namespace, pod_name)
    events = await mcp.fetch_pod_events(namespace, pod_name)
    
    evidence_item = {
        "source": "investigation",
        "pod": f"{namespace}/{pod_name}",
        "logs": logs,
        "events": events
    }

    if incident_id:
        await asyncio.to_thread(
            audit_logger.record_audit,
            AuditEntry(
                incident_id=incident_id,
                action=AuditAction.INVESTIGATION_COMPLETED,
                actor="ai-agent",
                details={"pod": pod_name, "namespace": namespace},
            ),
        )
    
    return {"evidence": [evidence_item], "messages": ["Investigation complete"]}
