from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from core.audit_logger import AuditLogger
from core.models import AuditAction, AuditEntry


@pytest.fixture()
def _isolated_audit(tmp_path, monkeypatch):
    """Replace the global audit_logger singleton with a tmp_path-backed instance."""
    isolated_logger = AuditLogger(sqlite_path=tmp_path / "test_audit.db")

    # Patch the singleton used by the metrics endpoint and the audit API
    import api.audit
    import api.metrics
    monkeypatch.setattr(api.metrics, "audit_logger", isolated_logger)
    monkeypatch.setattr(api.audit, "audit_logger", isolated_logger)
    return isolated_logger


@pytest.fixture()
def client():
    from main import app
    return TestClient(app)


@pytest.mark.usefixtures("_isolated_audit")
def test_dora_metrics(_isolated_audit, client):
    logger = _isolated_audit
    now = datetime.now(UTC)

    # Incident 1: 1 hour MTTR, 10 mins Lead Time
    logger.record_audit(AuditEntry(
        incident_id="inc-1", action=AuditAction.INCIDENT_CREATED, timestamp=now - timedelta(hours=1)
    ))
    logger.record_audit(AuditEntry(
        incident_id="inc-1", action=AuditAction.PATCH_PROPOSED, timestamp=now - timedelta(minutes=10)
    ))
    logger.record_audit(AuditEntry(
        incident_id="inc-1", action=AuditAction.PATCH_EXECUTED, timestamp=now
    ))
    logger.record_audit(AuditEntry(
        incident_id="inc-1", action=AuditAction.EVALUATION_COMPLETED, timestamp=now
    ))

    # Incident 2: 2 hours MTTR, 20 mins Lead Time
    logger.record_audit(AuditEntry(
        incident_id="inc-2", action=AuditAction.INCIDENT_CREATED, timestamp=now - timedelta(hours=2)
    ))
    logger.record_audit(AuditEntry(
        incident_id="inc-2", action=AuditAction.PATCH_PROPOSED, timestamp=now - timedelta(minutes=20)
    ))
    logger.record_audit(AuditEntry(
        incident_id="inc-2", action=AuditAction.PATCH_EXECUTED, timestamp=now
    ))
    logger.record_audit(AuditEntry(
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
