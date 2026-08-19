import logging
from agents.state import IncidentState

logger = logging.getLogger(__name__)

def triage_node(state: IncidentState) -> dict:
    """Deterministic 4-signal filter for incident severity."""
    logger.info(f"Running triage for incident {state.get('incident_id')}")
    
    event = state.get("raw_event", {})
    reason = event.get("reason", "")
    
    # 4-signal filter + 5 others for robustness
    critical_reasons = {
        "CrashLoopBackOff", "OOMKilled", "FailedCreate", 
        "FailedMount", "FailedScheduling", "BackOff", 
        "Unhealthy", "ImagePullBackOff", "ErrImagePull"
    }
    
    if reason in critical_reasons:
        return {"status": "INVESTIGATING", "messages": [f"Triage passed: {reason}"]}
    
    return {"status": "RESOLVED", "messages": [f"Triage filtered out: {reason}"]}
