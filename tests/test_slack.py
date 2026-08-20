from unittest.mock import MagicMock, patch

import httpx
import pytest

from core.slack import SlackClient


@pytest.fixture
def slack_client(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://test-webhook-url")
    return SlackClient()

@pytest.fixture
def slack_client_no_webhook(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    return SlackClient()

@pytest.mark.asyncio
async def test_send_proposal_notification_success(slack_client):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = await slack_client.send_proposal_notification("inc-123", "Out of memory", 0.95)
        
        assert result is True
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        
        payload = kwargs["json"]
        assert "attachments" in payload
        attachment = payload["attachments"][0]
        assert "inc-123" in attachment["fallback"]
        assert attachment["color"] == "#2EB67D"  # High confidence color
        assert "Out of memory" == attachment["fields"][0]["value"]
        assert "95%" in attachment["fields"][1]["value"]

@pytest.mark.asyncio
async def test_send_proposal_notification_low_confidence(slack_client):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = await slack_client.send_proposal_notification("inc-124", "Unknown error", 0.40)
        
        assert result is True
        _, kwargs = mock_post.call_args
        payload = kwargs["json"]
        assert payload["attachments"][0]["color"] == "#E01E5A"  # Low confidence color
        
@pytest.mark.asyncio
async def test_send_proposal_notification_disabled(slack_client_no_webhook):
    with patch("httpx.AsyncClient.post") as mock_post:
        result = await slack_client_no_webhook.send_proposal_notification("inc-123", "OOM", 0.9)
        assert result is False
        mock_post.assert_not_called()
        
@pytest.mark.asyncio
async def test_send_proposal_notification_error(slack_client):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = httpx.RequestError("Network error")
        
        result = await slack_client.send_proposal_notification("inc-123", "OOM", 0.9)
        
        assert result is False
