import logging
from agents.state import IncidentState
from core.mcp_client import mcp

logger = logging.getLogger(__name__)

async def investigate_node(state: IncidentState) -> dict:
    """Fetches pod logs and events using the MCP client."""
    logger.info(f"Running investigation for incident {state.get('incident_id')}")
    
    event = state.get("raw_event", {})
    involved = event.get("involved_object", {})
    
    namespace = involved.get("namespace", "default")
    pod_name = involved.get("name", "")
    
    if not pod_name:
        return {"messages": ["Investigation skipped: no pod name in event"]}
        
    try:
        logs = await mcp.fetch_pod_logs(namespace, pod_name)
        events = await mcp.fetch_pod_events(namespace, pod_name)
        
        evidence_item = {
            "source": "investigation",
            "pod": f"{namespace}/{pod_name}",
            "logs": logs,
            "events": events
        }
        
        return {"evidence": [evidence_item], "messages": ["Investigation complete"]}
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        return {"messages": [f"Investigation failed: {str(e)}"]}
