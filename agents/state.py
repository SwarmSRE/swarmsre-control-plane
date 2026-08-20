import operator
from typing import Annotated, Literal, TypedDict


class IncidentState(TypedDict, total=False):
    incident_id: str
    status: Literal["OPEN", "INVESTIGATING", "PROPOSED", "RESOLVED", "REJECTED"]
    raw_event: dict
    evidence: Annotated[list[dict], operator.add]
    log_hunter_output: dict | None
    telemetry_output: dict | None
    rca_summary: str | None
    proposed_patch: str | None
    confidence_score: float
    opa_result: dict | None
    messages: Annotated[list[str], operator.add]
