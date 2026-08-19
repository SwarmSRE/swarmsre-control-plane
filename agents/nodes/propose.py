import logging

from langgraph.types import interrupt

from agents.state import IncidentState

logger = logging.getLogger(__name__)

def propose_node(state: IncidentState) -> dict:
    """Proposes a remediation and pauses for human approval."""
    logger.info(f"Running propose for incident {state.get('incident_id')}")
    
    patch = state.get("proposed_patch", "")
    rca = state.get("rca_summary", "")
    confidence = state.get("confidence_score", 0.0)
    
    if not patch:
        return {"status": "RESOLVED", "messages": ["No patch proposed. Resolving."]}
    
    # Pause the graph and send the proposal to the human
    # The graph will wait here until `Command(resume=...)` is invoked
    human_decision = interrupt({
        "type": "PROPOSAL_READY",
        "incident_id": state.get("incident_id"),
        "rca_summary": rca,
        "proposed_patch": patch,
        "confidence_score": confidence,
        "action_required": "Please approve, modify, or reject this patch."
    })
    
    # Execution resumes here after human responds
    if human_decision.get("approved"):
        return {"status": "PROPOSED", "messages": ["Human approved the patch."]}
    else:
        return {"status": "REJECTED", "messages": ["Human rejected the patch."]}
