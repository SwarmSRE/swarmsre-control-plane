import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from agents.graph import app as langgraph_app
from agents.state import IncidentState
from api.websockets import manager
from core.audit_logger import audit_logger
from core.incident_store import incident_store
from core.models import (
    AuditAction,
    AuditEntry,
    Incident,
    IncidentCreate,
    IncidentResponse,
    IncidentStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

async def _run_incident_workflow(incident_id: str, initial_state: IncidentState, config: dict):
    """Executes the LangGraph multi-agent swarm and updates incident state in real-time."""
    incident = incident_store.get(incident_id)
    if incident:
        incident.status = IncidentStatus.INVESTIGATING
        incident.updated_at = datetime.now(UTC)
        incident_store.save(incident)
        await manager.broadcast({
            "type": "INCIDENT_UPDATED",
            "data": incident.model_dump(mode="json")
        })

    try:
        # Run multi-agent graph
        await langgraph_app.ainvoke(initial_state, config)  # type: ignore[call-overload]

        # Retrieve checkpointed state
        graph_state = await langgraph_app.aget_state(config)  # type: ignore[arg-type]
        values = graph_state.values if graph_state else {}

        incident = incident_store.get(incident_id)
        if incident:
            # 1. Update Core RCA & Patch Fields
            if values.get("rca_summary"):
                incident.rca_summary = values["rca_summary"]
            if values.get("proposed_patch"):
                incident.proposed_patch = values["proposed_patch"]
            if values.get("confidence_score") is not None:
                incident.confidence_score = float(values["confidence_score"])
            
            # 2. Update Structured Agent Outputs for UI Cards
            if values.get("log_hunter_output"):
                incident.log_hunter_output = values["log_hunter_output"]
            if values.get("telemetry_output"):
                incident.telemetry_output = values["telemetry_output"]
            if values.get("evidence"):
                incident.evidence_chain = [e if isinstance(e, dict) else {"details": str(e)} for e in values["evidence"]]
                
            # 3. Build Agent Trace for UI Expansion & CLI
            if values.get("messages"):
                trace = []
                for m in values["messages"]:
                    msg_str = str(m)
                    agent = "System"
                    if msg_str.startswith("["):
                        parts = msg_str.split("]", 1)
                        if len(parts) == 2:
                            agent = parts[0][1:]
                            msg_str = parts[1].strip()
                    trace.append({
                        "agent": agent,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "summary": msg_str[:150] + ("..." if len(msg_str) > 150 else ""),
                        "details": msg_str
                    })
                incident.agent_trace = trace

            # 4. State Management
            if incident.proposed_patch or (values.get("rca_summary") and values.get("status") != "REJECTED"):
                incident.status = IncidentStatus.PROPOSED
            elif values.get("status") in ["RESOLVED", "REJECTED"]:
                incident.status = IncidentStatus(values["status"])
            else:
                incident.status = IncidentStatus.PROPOSED

            incident.updated_at = datetime.now(UTC)
            incident_store.save(incident)

            # Broadcast the updated incident with RCA, Patch, and PROPOSED status
            await manager.broadcast({
                "type": "INCIDENT_UPDATED",
                "data": incident.model_dump(mode="json")
            })

    except Exception as e:
        # Fail loudly — mark FAILED and broadcast the error to the UI
        logger.exception(f"Incident workflow FAILED for {incident_id}")
        incident = incident_store.get(incident_id)
        if incident:
            incident.status = IncidentStatus.FAILED
            incident.updated_at = datetime.now(UTC)
            incident_store.save(incident)
            await manager.broadcast({
                "type": "INCIDENT_FAILED",
                "data": {
                    **incident.model_dump(mode="json"),
                    "error": str(e),
                }
            })
        raise


@router.post("", response_model=IncidentResponse)
async def create_incident(incident_in: IncidentCreate):
    incident = Incident(
        title=incident_in.title,
        description=incident_in.description,
        source=incident_in.source,
        raw_event=incident_in.raw_event
    )
    incident_store.save(incident)
    
    # Broadcast new incident to dashboard
    await manager.broadcast({
        "type": "INCIDENT_CREATED",
        "data": incident.model_dump(mode='json')
    })
    
    # Audit log
    await asyncio.to_thread(
        audit_logger.record_audit,
        AuditEntry(
            incident_id=incident.id,
            action=AuditAction.INCIDENT_CREATED,
            details={"title": incident.title, "source": incident.source},
        ),
    )
    
    # Trigger LangGraph state machine in the background
    initial_state: IncidentState = {
        "incident_id": incident.id,
        "status": incident.status.value,  # type: ignore[typeddict-item]
        "raw_event": incident.raw_event or {},
        "evidence": [],
        "messages": [f"[System] Incident {incident.id} created"]
    }
    config = {"configurable": {"thread_id": incident.id}}
    asyncio.create_task(_run_incident_workflow(incident.id, initial_state, config))
    
    return incident

@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    incident = incident_store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.get("", response_model=list[IncidentResponse])
async def list_incidents():
    return incident_store.list_all()

@router.post("/{incident_id}/approve", response_model=IncidentResponse)
async def approve_incident(incident_id: str):
    incident = incident_store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.status != IncidentStatus.PROPOSED:
        raise HTTPException(status_code=400, detail=f"Cannot approve incident in {incident.status.value} state")
        
    # Update state
    incident.status = IncidentStatus.RESOLVED
    incident.updated_at = datetime.now(UTC)
    incident_store.save(incident)
    
    # Broadcast update
    await manager.broadcast({
        "type": "INCIDENT_UPDATED",
        "data": incident.model_dump(mode='json')
    })
    
    # Audit log
    await asyncio.to_thread(
        audit_logger.record_audit,
        AuditEntry(
            incident_id=incident_id,
            action=AuditAction.PATCH_APPROVED,
            actor="human-approver",
        ),
    )
    
    # Resume LangGraph execution from the HITL pause node to apply patch
    config = {"configurable": {"thread_id": incident_id}}
    asyncio.create_task(langgraph_app.ainvoke(Command(resume={"approved": True}), config))  # type: ignore[call-overload]
    
    return incident

@router.post("/{incident_id}/reject", response_model=IncidentResponse)
async def reject_incident(incident_id: str):
    incident = incident_store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.status != IncidentStatus.PROPOSED:
        raise HTTPException(status_code=400, detail=f"Cannot reject incident in {incident.status.value} state")
        
    # Update state
    incident.status = IncidentStatus.REJECTED
    incident.updated_at = datetime.now(UTC)
    incident_store.save(incident)
    
    # Broadcast update
    await manager.broadcast({
        "type": "INCIDENT_UPDATED",
        "data": incident.model_dump(mode='json')
    })
    
    # Audit log
    await asyncio.to_thread(
        audit_logger.record_audit,
        AuditEntry(
            incident_id=incident_id,
            action=AuditAction.PATCH_REJECTED,
            actor="human-approver",
        ),
    )
    
    # Resume LangGraph execution with a rejection
    config = {"configurable": {"thread_id": incident_id}}
    asyncio.create_task(langgraph_app.ainvoke(Command(resume={"approved": False}), config))  # type: ignore[call-overload]
    
    return incident

async def on_incident_detected(incident_data: dict):
    """Callback for the Kubernetes event watcher."""
    incident_in = IncidentCreate(
        title=f"K8s Event: {incident_data.get('reason', 'Unknown')} in {incident_data.get('namespace', 'unknown')}",
        description=incident_data.get("message", "No message provided."),
        source="kubernetes-watcher",
        raw_event=incident_data
    )
    await create_incident(incident_in)

