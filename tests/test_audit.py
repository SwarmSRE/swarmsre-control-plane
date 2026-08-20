from datetime import UTC, datetime

from core.audit_logger import audit_logger
from core.models import AuditAction, AuditEntry


def test_record_and_retrieve_audit():
    entry = AuditEntry(
        incident_id="inc-123",
        action=AuditAction.INCIDENT_CREATED,
        actor="test-system",
        details={"foo": "bar"}
    )
    audit_logger.record_audit(entry)

    entries = audit_logger.get_entries_for_incident("inc-123")
    assert len(entries) == 1
    assert entries[0].incident_id == "inc-123"
    assert entries[0].action == AuditAction.INCIDENT_CREATED
    assert entries[0].actor == "test-system"
    assert entries[0].details == {"foo": "bar"}

def test_get_all_entries_order():
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
    audit_logger.record_audit(entry2)
    audit_logger.record_audit(entry1)

    entries = audit_logger.get_all_entries()
    assert len(entries) == 2
    # Should be sorted by timestamp ASC
    assert entries[0].action == AuditAction.INCIDENT_CREATED
    assert entries[1].action == AuditAction.TRIAGE_COMPLETED
