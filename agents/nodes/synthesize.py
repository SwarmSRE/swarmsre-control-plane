import json
import logging
import typing

from pydantic import BaseModel, Field

from agents.prompts.synthesize_prompt import synthesize_prompt
from agents.state import IncidentState
from core.llm import get_orchestrator_llm

logger = logging.getLogger(__name__)

class RCASummary(BaseModel):
    """Structured root cause analysis summary and confidence score."""
    rca_summary: str = Field(
        description="A cohesive, concise summary of the root cause based on all findings."
    )
    confidence_score: float = Field(
        description="A score between 0.0 and 1.0 indicating confidence in the root cause."
    )
    proposed_patch: str | None = Field(
        description="A Kubernetes YAML patch (in plain text) that resolves the root cause, or None if no patch can be proposed."
    )

async def synthesize_node(state: IncidentState) -> dict:
    """Synthesizes evidence from multiple agents into an RCA using the orchestrator LLM asynchronously."""
    incident_id = state.get("incident_id")
    logger.info(f"Running async synthesis for incident {incident_id}")
    
    raw_event = state.get("raw_event", {})
    reason = raw_event.get("reason", "Unknown")
    involved = raw_event.get("involved_object", {})
    target_resource = json.dumps(involved) if involved else "Unknown"
    
    log_hunter_output = state.get("log_hunter_output", {})
    telemetry_output = state.get("telemetry_output", {})

    llm = get_orchestrator_llm()
    structured_llm = llm.with_structured_output(RCASummary)
    chain = synthesize_prompt | structured_llm
    
    result = typing.cast(RCASummary, await chain.ainvoke({
        "target_resource": target_resource,
        "reason": reason,
        "log_hunter_output": json.dumps(log_hunter_output),
        "telemetry_output": json.dumps(telemetry_output)
    }))
    
    logger.info(f"Synthesis complete. Confidence: {result.confidence_score}")
    
    return {
        "rca_summary": result.rca_summary,
        "confidence_score": result.confidence_score,
        "proposed_patch": result.proposed_patch,
        "messages": [f"[Supervisor] Synthesized findings into root cause analysis with {result.confidence_score * 100:.0f}% confidence."]
    }
