import logging

from agents.state import IncidentState

logger = logging.getLogger(__name__)

def execute_node(state: IncidentState) -> dict:
    """Executes the approved patch (Phase B)."""
    logger.info(f"Running execute for incident {state.get('incident_id')}")
    
    if state.get("status") == "REJECTED":
        return {"messages": ["Execution skipped because patch was rejected."]}
        
    return {"messages": ["Execution complete (placeholder)"]}
