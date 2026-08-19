import operator
from typing import Annotated, Literal, TypedDict


class IncidentState(TypedDict):
    incident_id: str
    status: Literal["OPEN", "INVESTIGATING", "PROPOSED", "RESOLVED", "REJECTED"]
    raw_event: dict
    evidence: Annotated[list[dict], operator.add]
    rca_summary: str | None
    proposed_patch: str | None
    confidence_score: float
    messages: Annotated[list[str], operator.add]
