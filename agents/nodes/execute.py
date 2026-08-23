import logging

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.mcp_client import mcp
from core.models import AuditAction, AuditEntry

logger = logging.getLogger(__name__)

async def execute_node(state: IncidentState) -> dict:
    """Executes the approved patch via MCP."""
    incident_id = state.get("incident_id")
    logger.info(f"Running execute for incident {incident_id}")
    
    if state.get("status") == "REJECTED":
        return {"messages": ["Execution skipped because patch was rejected."]}

    patch = state.get("proposed_patch")
    if not patch:
        return {"messages": ["Execution skipped because no patch was proposed."]}

    output = await mcp.apply_patch(patch)
    
    if incident_id:
        audit_logger.record_audit(AuditEntry(
            incident_id=incident_id,
            action=AuditAction.PATCH_EXECUTED,
            actor="ai-agent",
            details={"output": output}
        ))
        
    return {"messages": [f"Execution complete: {output}"]}
