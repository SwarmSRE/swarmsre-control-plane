from collections import defaultdict

from fastapi import APIRouter

from core.audit_logger import audit_logger
from core.models import AuditAction

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/dora")
def get_dora_metrics():
    """
    Calculates pseudo-DORA metrics based on the SwarmSRE audit trail:
    - MTTR (Mean Time to Recovery): Average time from INCIDENT_CREATED to EVALUATION_COMPLETED.
    - Lead Time for Changes: Average time from PATCH_PROPOSED to PATCH_EXECUTED.
    """
    entries = audit_logger.get_all_entries()
    
    # Group by incident_id, keeping all timestamps per action
    incident_timings: dict[str, dict[AuditAction, list]] = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        incident_timings[entry.incident_id][entry.action].append(entry.timestamp)

    mttr_seconds = []
    lead_time_seconds = []

    for timings in incident_timings.values():
        # MTTR: earliest INCIDENT_CREATED -> latest EVALUATION_COMPLETED
        if AuditAction.INCIDENT_CREATED in timings and AuditAction.EVALUATION_COMPLETED in timings:
            start = min(timings[AuditAction.INCIDENT_CREATED])
            end = max(timings[AuditAction.EVALUATION_COMPLETED])
            mttr_seconds.append((end - start).total_seconds())
            
        # Lead Time: earliest PATCH_PROPOSED -> latest PATCH_EXECUTED
        if AuditAction.PATCH_PROPOSED in timings and AuditAction.PATCH_EXECUTED in timings:
            start = min(timings[AuditAction.PATCH_PROPOSED])
            end = max(timings[AuditAction.PATCH_EXECUTED])
            lead_time_seconds.append((end - start).total_seconds())
            
    avg_mttr = sum(mttr_seconds) / len(mttr_seconds) if mttr_seconds else 0.0
    avg_lead_time = sum(lead_time_seconds) / len(lead_time_seconds) if lead_time_seconds else 0.0

    return {
        "metrics": {
            "mean_time_to_recovery_seconds": round(avg_mttr, 2),
            "lead_time_for_changes_seconds": round(avg_lead_time, 2),
            "total_incidents_resolved": len(mttr_seconds),
            "total_patches_executed": len(lead_time_seconds)
        }
    }
