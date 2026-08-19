import logging

from agents.state import IncidentState

logger = logging.getLogger(__name__)

def evaluate_node(state: IncidentState) -> dict:
    """Evaluates the success of the execution (Phase B)."""
    logger.info(f"Running evaluate for incident {state.get('incident_id')}")
    
    if state.get("status") == "REJECTED":
        return {"messages": ["Evaluation skipped because patch was rejected."]}
        
    return {"status": "RESOLVED", "messages": ["Evaluation complete (placeholder)"]}
