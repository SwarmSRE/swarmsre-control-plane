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
        default_factory=list,
        description="Specific signals indicating saturation or resource constraints."
    )
    anomalies: list[str] = Field(
        default_factory=list,
        description="List of any other anomalies detected in the status or events, or empty list if none."
    )

async def telemetry_analyst_node(state: IncidentState) -> dict:
    """Fetches telemetry via MCP and analyzes it using the worker LLM asynchronously."""
    incident_id = state.get("incident_id")
    logger.info(f"Running async Telemetry Analyst for incident {incident_id}")
    
    event = state.get("raw_event", {})
    involved = event.get("involved_object", {})
    
    namespace = involved.get("namespace", "default")
    pod_name = involved.get("name", "")
    
    if not pod_name:
        raise ValueError(f"Telemetry Analyst failed for {incident_id}: no pod name in event")
        
    # Fetch telemetry and status concurrently
    top_task = asyncio.create_task(mcp.fetch_pod_top(namespace, pod_name))
    status_task = asyncio.create_task(mcp.fetch_pod_status(namespace, pod_name))
    
    top_data, status_data = await asyncio.gather(top_task, status_task)
    
    telemetry = f"Top:\n{top_data}\n\nStatus:\n{status_data}"
    reason = event.get("reason", "Unknown")
    
    # Use events from evidence if available
    evidence = state.get("evidence", [])
    inv_evidence = next((e for e in reversed(evidence) if e.get("source") == "investigation"), None)
    events_str = inv_evidence.get("events", "") if inv_evidence else ""
    
    llm = get_worker_llm()
    structured_llm = llm.with_structured_output(TelemetryOutput)
    chain = telemetry_analyst_prompt | structured_llm
    
    result = typing.cast(TelemetryOutput, await chain.ainvoke({
        "reason": reason,
        "telemetry": telemetry[:4000],  # Truncate if too long
        "events": events_str[:2000]
    }))
    
    logger.info(f"Telemetry Analyst extracted resource_status: {result.resource_status}")
    
    return {
        "telemetry_output": result.model_dump(),
        "messages": [f"[Telemetry Analyst] Resource status: '{result.resource_status}'. {len(result.anomalies)} anomalies detected."]
    }
