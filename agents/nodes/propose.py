import logging

import yaml
from langgraph.types import interrupt

from agents.state import IncidentState
from core.audit_logger import audit_logger
from core.models import AuditAction, AuditEntry
from core.safety_gate import validate_kubernetes_patch
from core.slack import slack_client

logger = logging.getLogger(__name__)

async def propose_node(state: IncidentState) -> dict:
    """Proposes a remediation, checks safety, and pauses for human approval."""
    incident_id = state.get("incident_id")
    logger.info(f"Running propose for incident {incident_id}")
    
    patch = state.get("proposed_patch") or ""
    rca = state.get("rca_summary") or ""
    confidence = state.get("confidence_score", 0.0)
    
    if not patch:
        return {"status": "RESOLVED", "messages": ["No patch proposed. Resolving."]}

    # OPA Safety Gate
    opa_result = {"passed": True, "denials": []}
    try:
        patch_dict = yaml.safe_load(patch)
        if not isinstance(patch_dict, dict):
            raise TypeError("Patch must be a YAML object.")
        
        denials = validate_kubernetes_patch(patch_dict)
        if denials:
            opa_result["passed"] = False
            opa_result["denials"] = denials
            logger.warning(f"Patch rejected by OPA safety gate: {denials}")
    except Exception as e:
        opa_result["passed"] = False
        opa_result["denials"] = [f"Failed to parse or validate patch: {e!s}"]
        logger.error(f"Safety gate evaluation error: {e}")

    if not opa_result["passed"]:
        if incident_id:
            audit_logger.record_audit(AuditEntry(
                incident_id=incident_id,
                action=AuditAction.PATCH_REJECTED,
                actor="system(opa)",
                details={"denials": opa_result["denials"]}
            ))
        return {
            "status": "REJECTED",
            "opa_result": opa_result,
            "messages": [f"Patch rejected by safety gate: {opa_result['denials']}"]
        }

    if incident_id:
        audit_logger.record_audit(AuditEntry(
            incident_id=incident_id,
            action=AuditAction.PATCH_PROPOSED,
            actor="ai-agent",
            details={"rca": rca, "confidence": confidence}
        ))
        
        await slack_client.send_proposal_notification(incident_id, rca, confidence)
    
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
