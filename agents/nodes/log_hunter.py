import logging
import typing
from typing import Literal

from pydantic import BaseModel, Field

from agents.prompts.log_hunter_prompt import log_hunter_prompt
from agents.state import IncidentState
from core.llm import get_worker_llm

logger = logging.getLogger(__name__)

class LogHunterOutput(BaseModel):
    """Structured insights extracted from raw pod logs and events."""
    error_class: str = Field(
        description="The high-level class of the error (e.g., 'OOMKilled', 'ConnectionRefused', 'CrashLoopBackOff')."
    )
    stack_trace: str | None = Field(
        description="The relevant stack trace extracted from the logs, or None if not present."
    )
    frequency: Literal["isolated", "frequent", "constant"] = Field(
        description="How often the error appears in the logs."
    )
    first_seen: str | None = Field(
        description="Approximate timestamp or context of when the error first appeared, or None."
    )

def log_hunter_node(state: IncidentState) -> dict:
    """Analyzes evidence logs using the worker LLM to extract structured insights."""
    incident_id = state.get("incident_id")
    logger.info(f"Running Log Hunter for incident {incident_id}")
    
    evidence = state.get("evidence", [])
    if not evidence:
        return {"messages": ["Log Hunter skipped: no evidence available."]}
        
    # Get the latest investigation evidence
    inv_evidence = next((e for e in reversed(evidence) if e.get("source") == "investigation"), None)
    if not inv_evidence:
        return {"messages": ["Log Hunter skipped: no investigation evidence found."]}
        
    logs = inv_evidence.get("logs", "")
    events = inv_evidence.get("events", "")
    reason = state.get("raw_event", {}).get("reason", "Unknown")
    
    if not logs and not events:
        return {"messages": ["Log Hunter skipped: logs and events are empty."]}
        
    try:
        llm = get_worker_llm()
        structured_llm = llm.with_structured_output(LogHunterOutput)
        chain = log_hunter_prompt | structured_llm
        
        result = typing.cast(LogHunterOutput, chain.invoke({
            "reason": reason,
            "logs": logs[:4000],  # Truncate logs if they are too long
            "events": events
        }))
        
        logger.info(f"Log Hunter extracted error_class: {result.error_class}")
        
        return {
            "log_hunter_output": result.model_dump(),
            "messages": [f"Log Hunter identified error class: {result.error_class}"]
        }
    except Exception as e:
        logger.error(f"Log Hunter failed: {e}")
        return {"messages": [f"Log Hunter failed: {e!s}"]}
