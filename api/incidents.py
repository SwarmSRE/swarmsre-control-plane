import asyncio
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from agents.graph import app as langgraph_app
from agents.state import IncidentState
from api.websockets import manager
from core.audit_logger import audit_logger
from core.models import (
    AuditAction,
    AuditEntry,
    Incident,
    IncidentCreate,
    IncidentResponse,
    IncidentStatus,
)

logger = logging.getLogger(__name__)

def _log_task_result(task: asyncio.Task):
    try:
        task.result()
    except Exception as e:
        logger.error(f"Background task failed: {e}")

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

# In-memory store for MVP
# In a production scenario this would be a database (PostgreSQL, MongoDB)
db: dict[str, Incident] = {}

@router.post("", response_model=IncidentResponse)
async def create_incident(incident_in: IncidentCreate):
    incident = Incident(
        title=incident_in.title,
        description=incident_in.description,
        source=incident_in.source,
        raw_event=incident_in.raw_event
    )
    db[incident.id] = incident
    
    # Broadcast new incident to dashboard
    await manager.broadcast({
        "type": "INCIDENT_CREATED",
        "data": incident.model_dump(mode='json')
    })
    
    # Audit log (offloaded to thread to avoid blocking the event loop)
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
        "status": incident.status.value,  # type: ignore
        "raw_event": incident.raw_event or {},
        "evidence": [],
        "messages": [f"Incident {incident.id} created"]
    }
    config = {"configurable": {"thread_id": incident.id}}
    task = asyncio.create_task(langgraph_app.ainvoke(initial_state, config)) # type: ignore
    task.add_done_callback(_log_task_result)
    
    return incident

@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    if incident_id not in db:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db[incident_id]

@router.get("", response_model=list[IncidentResponse])
async def list_incidents():
    return list(db.values())

@router.post("/{incident_id}/approve", response_model=IncidentResponse)
async def approve_incident(incident_id: str):
    """
    HITL Endpoint: User approves the proposed YAML patch.
    """
    if incident_id not in db:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    incident = db[incident_id]
    
    if incident.status != IncidentStatus.PROPOSED:
        raise HTTPException(status_code=400, detail=f"Cannot approve incident in {incident.status.value} state")
        
    # Update state
    incident.status = IncidentStatus.RESOLVED
    incident.updated_at = datetime.now(UTC)
    db[incident_id] = incident
    
    # Broadcast update
    await manager.broadcast({
        "type": "INCIDENT_UPDATED",
        "data": incident.model_dump(mode='json')
    })
    
    # Audit log (offloaded to thread to avoid blocking the event loop)
    await asyncio.to_thread(
        audit_logger.record_audit,
        AuditEntry(
            incident_id=incident_id,
            action=AuditAction.PATCH_APPROVED,
            actor="human-approver",
        ),
    )
    
    # Resume LangGraph execution from the HITL pause node
    config = {"configurable": {"thread_id": incident_id}}
    task = asyncio.create_task(langgraph_app.ainvoke(Command(resume={"approved": True}), config)) # type: ignore
    task.add_done_callback(_log_task_result)
    
    return incident

@router.post("/{incident_id}/reject", response_model=IncidentResponse)
async def reject_incident(incident_id: str):
    """
    HITL Endpoint: User rejects the proposed YAML patch.
    """
    if incident_id not in db:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    incident = db[incident_id]
    
    if incident.status != IncidentStatus.PROPOSED:
        raise HTTPException(status_code=400, detail=f"Cannot reject incident in {incident.status.value} state")
        
    # Update state
    incident.status = IncidentStatus.REJECTED
    incident.updated_at = datetime.now(UTC)
    db[incident_id] = incident
    
    # Broadcast update
    await manager.broadcast({
        "type": "INCIDENT_UPDATED",
        "data": incident.model_dump(mode='json')
    })
    
    # Audit log (offloaded to thread to avoid blocking the event loop)
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
    task = asyncio.create_task(langgraph_app.ainvoke(Command(resume={"approved": False}), config)) # type: ignore
    task.add_done_callback(_log_task_result)
    
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
