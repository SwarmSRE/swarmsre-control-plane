import asyncio
import logging
import typing
from typing import Literal

from pydantic import BaseModel, Field

from agents.prompts.telemetry_analyst_prompt import telemetry_analyst_prompt
from agents.state import IncidentState
from core.llm import get_worker_llm
from core.mcp_client import mcp

logger = logging.getLogger(__name__)

class TelemetryOutput(BaseModel):
    """Structured insights extracted from pod telemetry and status."""
    resource_status: Literal["healthy", "cpu_saturation", "memory_saturation", "throttled", "unknown"] = Field(
        description="The high-level status of the pod's resources."
    )
    saturation_signals: list[str] = Field(
        description="Specific signals indicating saturation or resource constraints."
    )
    anomalies: str | None = Field(
        description="Any other anomalies detected in the status or events, or None if healthy."
    )

async def telemetry_analyst_node(state: IncidentState) -> dict:
    """Fetches telemetry via MCP and analyzes it using the worker LLM."""
    incident_id = state.get("incident_id")
    logger.info(f"Running Telemetry Analyst for incident {incident_id}")
    
    event = state.get("raw_event", {})
    involved = event.get("involved_object", {})
    
    namespace = involved.get("namespace", "default")
    pod_name = involved.get("name", "")
    
    if not pod_name:
        return {"messages": ["Telemetry Analyst skipped: no pod name in event"]}
        
    try:
        # Fetch telemetry and status concurrently
        top_task = asyncio.create_task(mcp.fetch_pod_top(namespace, pod_name))
        status_task = asyncio.create_task(mcp.fetch_pod_status(namespace, pod_name))
        
        top_data, status_data = await asyncio.gather(top_task, status_task)
        
        telemetry = f"Top:\n{top_data}\n\nStatus:\n{status_data}"
        reason = event.get("reason", "Unknown")
        
        # We can also pass events if they were fetched in investigate, but for simplicity we fetch them or just use the reason.
        # Actually, let's use the events from evidence if available.
        evidence = state.get("evidence", [])
        inv_evidence = next((e for e in reversed(evidence) if e.get("source") == "investigation"), None)
        events_str = inv_evidence.get("events", "") if inv_evidence else ""
        
        llm = get_worker_llm()
        structured_llm = llm.with_structured_output(TelemetryOutput)
        chain = telemetry_analyst_prompt | structured_llm
        
        result = typing.cast(TelemetryOutput, chain.invoke({
            "reason": reason,
            "telemetry": telemetry[:4000],  # Truncate if too long
            "events": events_str[:2000]
        }))
        
        logger.info(f"Telemetry Analyst extracted resource_status: {result.resource_status}")
        
        return {
            "telemetry_output": result.model_dump(),
            "messages": [f"Telemetry Analyst identified resource status: {result.resource_status}"]
        }
    except Exception as e:
        logger.error(f"Telemetry Analyst failed: {e}")
        return {"messages": [f"Telemetry Analyst failed: {e!s}"]}
