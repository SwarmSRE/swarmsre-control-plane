"""Global test fixtures — patches the audit_logger singleton with an in-memory backend."""

import os

# Must be set before importing the app so MCPClient() doesn't raise at module level.
# In CI, MCP is not running; all MCP calls are patched per-test.
os.environ.setdefault("MCP_SERVER_URL", "http://localhost:3000")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-ci")
os.environ.setdefault("OPENAI_API_KEY", "test-key-ci")

import pytest
from fastapi.testclient import TestClient

from core.models import AuditEntry
from main import app


class InMemoryBackend:
    """In-memory backend for tests — no database needed."""

    def __init__(self):
        self._entries: list[AuditEntry] = []

    def record_audit(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def get_entries_for_incident(self, incident_id: str) -> list[AuditEntry]:
        return sorted(
            [e for e in self._entries if e.incident_id == incident_id],
            key=lambda e: e.timestamp,
        )

    def get_all_entries(self) -> list[AuditEntry]:
        return sorted(self._entries, key=lambda e: e.timestamp)


@pytest.fixture(autouse=True)
def _patch_audit_logger(monkeypatch):
    """Auto-patch the global audit_logger with an in-memory backend for every test."""
    import core.audit_logger as audit_module

    in_mem = InMemoryBackend()
    monkeypatch.setattr(audit_module.audit_logger, "_backend", in_mem)

@pytest.fixture
def test_client():
    """Provides a FastAPI TestClient."""
    return TestClient(app)
