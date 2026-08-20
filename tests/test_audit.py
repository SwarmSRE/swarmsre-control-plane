from datetime import UTC, datetime

import pytest

from core.audit_logger import AuditLogger
from core.models import AuditAction, AuditEntry


@pytest.fixture
def mock_logger(tmp_path):
    db_path = tmp_path / "test_audit.db"
    return AuditLogger(sqlite_path=db_path)

def test_record_and_retrieve_audit(mock_logger):
    entry = AuditEntry(
        incident_id="inc-123",
        action=AuditAction.INCIDENT_CREATED,
        actor="test-system",
        details={"foo": "bar"}
    )
    mock_logger.record_audit(entry)

    entries = mock_logger.get_entries_for_incident("inc-123")
    assert len(entries) == 1
    assert entries[0].incident_id == "inc-123"
    assert entries[0].action == AuditAction.INCIDENT_CREATED
    assert entries[0].actor == "test-system"
    assert entries[0].details == {"foo": "bar"}

def test_get_all_entries_order(mock_logger):
    entry1 = AuditEntry(
        incident_id="inc-1",
        action=AuditAction.INCIDENT_CREATED,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC)
    )
    entry2 = AuditEntry(
        incident_id="inc-1",
        action=AuditAction.TRIAGE_COMPLETED,
        timestamp=datetime(2026, 1, 2, tzinfo=UTC)
    )
    
    # Insert out of order
    mock_logger.record_audit(entry2)
    mock_logger.record_audit(entry1)

    entries = mock_logger.get_all_entries()
    assert len(entries) == 2
    # Should be sorted by timestamp ASC
    assert entries[0].action == AuditAction.INCIDENT_CREATED
    assert entries[1].action == AuditAction.TRIAGE_COMPLETED
