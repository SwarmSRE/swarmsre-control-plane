from typing import TypedDict, Annotated, Literal, Optional
import operator

class IncidentState(TypedDict):
    incident_id: str
    status: Literal["OPEN", "INVESTIGATING", "PROPOSED", "RESOLVED", "REJECTED"]
    raw_event: dict
    evidence: Annotated[list[dict], operator.add]
    rca_summary: Optional[str]
    proposed_patch: Optional[str]
    confidence_score: float
    messages: Annotated[list[str], operator.add]
