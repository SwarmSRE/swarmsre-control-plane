from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from core.models import Incident, IncidentCreate, IncidentResponse, IncidentStatus
from api.websockets import manager

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

# In-memory store for MVP
# In a production scenario this would be a database (PostgreSQL, MongoDB)
db: Dict[str, Incident] = {}

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
    
    # In Day 3/4, this is where we will trigger the LangGraph state machine execution!
    
    return incident

@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    if incident_id not in db:
        raise HTTPException(status_code=404, detail="Incident not found")
    return db[incident_id]

@router.get("", response_model=List[IncidentResponse])
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
        raise HTTPException(status_code=400, detail=f"Cannot approve incident in {incident.status} state")
        
    # Update state
    incident.status = IncidentStatus.RESOLVED
    db[incident_id] = incident
    
    # Broadcast update
    await manager.broadcast({
        "type": "INCIDENT_UPDATED",
        "data": incident.model_dump(mode='json')
    })
    
    # In Day 8, this will trigger the LangGraph execution to resume from the (pause) node
    
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
        raise HTTPException(status_code=400, detail=f"Cannot reject incident in {incident.status} state")
        
    # Update state
    incident.status = IncidentStatus.REJECTED
    db[incident_id] = incident
    
    # Broadcast update
    await manager.broadcast({
        "type": "INCIDENT_UPDATED",
        "data": incident.model_dump(mode='json')
    })
    
    # In Day 8, this will trigger LangGraph to refine or close the incident
    
    return incident
