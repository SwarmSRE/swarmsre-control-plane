from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from core.audit_logger import audit_logger
from core.models import AuditAction, AuditEntry
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    # Because we're using a singleton in the app, we have to clear the table
    import sqlite3
    with sqlite3.connect(audit_logger.db_path) as conn:
        conn.execute("DELETE FROM audit_entries")
    yield
    with sqlite3.connect(audit_logger.db_path) as conn:
        conn.execute("DELETE FROM audit_entries")

def test_dora_metrics():
    # Insert some dummy records
    now = datetime.now(UTC)
    
    # Incident 1: 1 hour MTTR, 10 mins Lead Time
    audit_logger.record_audit(AuditEntry(
        incident_id="inc-1", action=AuditAction.INCIDENT_CREATED, timestamp=now - timedelta(hours=1)
    ))
    audit_logger.record_audit(AuditEntry(
        incident_id="inc-1", action=AuditAction.PATCH_PROPOSED, timestamp=now - timedelta(minutes=10)
    ))
    audit_logger.record_audit(AuditEntry(
        incident_id="inc-1", action=AuditAction.PATCH_EXECUTED, timestamp=now
    ))
    audit_logger.record_audit(AuditEntry(
        incident_id="inc-1", action=AuditAction.EVALUATION_COMPLETED, timestamp=now
    ))
    
    # Incident 2: 2 hours MTTR, 20 mins Lead Time
    audit_logger.record_audit(AuditEntry(
        incident_id="inc-2", action=AuditAction.INCIDENT_CREATED, timestamp=now - timedelta(hours=2)
    ))
    audit_logger.record_audit(AuditEntry(
        incident_id="inc-2", action=AuditAction.PATCH_PROPOSED, timestamp=now - timedelta(minutes=20)
    ))
    audit_logger.record_audit(AuditEntry(
        incident_id="inc-2", action=AuditAction.PATCH_EXECUTED, timestamp=now
    ))
    audit_logger.record_audit(AuditEntry(
        incident_id="inc-2", action=AuditAction.EVALUATION_COMPLETED, timestamp=now
    ))

    response = client.get("/api/metrics/dora")
    assert response.status_code == 200
    data = response.json()
    metrics = data["metrics"]
    
    # Average MTTR: (1 hr + 2 hrs) / 2 = 1.5 hrs = 5400 seconds
    assert metrics["mean_time_to_recovery_seconds"] == 5400.0
    
    # Average Lead Time: (10 mins + 20 mins) / 2 = 15 mins = 900 seconds
    assert metrics["lead_time_for_changes_seconds"] == 900.0
    
    assert metrics["total_incidents_resolved"] == 2
    assert metrics["total_patches_executed"] == 2
