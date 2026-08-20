import logging
import os

import httpx

logger = logging.getLogger(__name__)

class SlackClient:
    def __init__(self):
        self.webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        self.dashboard_url = os.environ.get("DASHBOARD_URL", "http://localhost:5173")

    async def send_proposal_notification(self, incident_id: str, rca_summary: str, confidence_score: float) -> bool:
        """Sends a Slack notification when a patch is proposed and awaiting approval."""
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL is not set. Skipping Slack notification.")
            return False

        incident_url = f"{self.dashboard_url}/incidents/{incident_id}"
        
        # Color coding based on confidence
        color = "#2EB67D" if confidence_score >= 0.8 else "#E01E5A" if confidence_score < 0.5 else "#ECB22E"

        payload = {
            "attachments": [
                {
                    "fallback": f"New Incident Proposal: {incident_id}",
                    "color": color,
                    "title": f"🚨 SwarmSRE: New Patch Proposal for {incident_id}",
                    "title_link": incident_url,
                    "text": "The AI orchestrator has generated a root cause analysis and a proposed patch.",
                    "fields": [
                        {
                            "title": "Root Cause Analysis",
                            "value": rca_summary,
                            "short": False
                        },
                        {
                            "title": "Confidence Score",
                            "value": f"{confidence_score:.0%}",
                            "short": True
                        },
                        {
                            "title": "Action Required",
                            "value": f"<{incident_url}|Review and Approve in Dashboard>",
                            "short": False
                        }
                    ],
                    "footer": "SwarmSRE AI Control Plane",
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Successfully sent Slack notification for incident {incident_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

slack_client = SlackClient()
