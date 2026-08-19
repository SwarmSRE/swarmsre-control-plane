from datetime import datetime

from core.models import Incident, IncidentCreate, IncidentStatus


def test_incident_creation():
    incident_in = IncidentCreate(
        title="Test Incident",
        description="Test description",
        source="kubernetes-watcher"
    )
    incident = Incident(
        title=incident_in.title,
        description=incident_in.description,
        source=incident_in.source,
        raw_event=incident_in.raw_event
    )
    assert incident.title == "Test Incident"
    assert incident.status == IncidentStatus.OPEN
    assert isinstance(incident.created_at, datetime)
