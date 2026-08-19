import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self):
        self.base_url = os.environ.get("MCP_SERVER_URL", "http://localhost:3000")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict[str, Any]:
        """Call an MCP tool via the HTTP/SSE interface."""
        # For this prototype, we're assuming a simple HTTP wrapper around the MCP server
        # In a real setup, this might use the official MCP Python SDK
        try:
            # Assuming a generic /tools/{tool_name}/execute endpoint for simplicity
            response = await self.client.post(
                f"/tools/{tool_name}/execute",
                json={"arguments": arguments}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error communicating with MCP server: {e}")
            return {"error": str(e), "status": "failed"}
        except httpx.HTTPStatusError as e:
            logger.error(f"MCP server returned error status {e.response.status_code}")
            return {"error": e.response.text, "status": "failed"}

    async def call_kubectl(self, command: str) -> str:
        """Call the kubectl tool on the MCP server."""
        logger.info(f"Calling MCP kubectl: {command}")
        result = await self._call_tool("call_kubectl", {"command": command})
        
        # Parse the standard MCP tool response format
        if result.get("status") == "failed":
            raise RuntimeError(f"MCP kubectl failed: {result.get('error')}")
            
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0].get("text", "")
        return str(result)

    async def fetch_pod_logs(self, namespace: str, pod_name: str) -> str:
        """Fetch the last 100 lines of logs for a pod."""
        command = f"kubectl logs {pod_name} -n {namespace} --tail=100"
        return await self.call_kubectl(command)

    async def fetch_pod_events(self, namespace: str, pod_name: str) -> str:
        """Fetch events involving a specific pod."""
        command = f"kubectl get events -n {namespace} --field-selector involvedObject.name={pod_name}"
        return await self.call_kubectl(command)

    async def fetch_pod_status(self, namespace: str, pod_name: str) -> str:
        """Fetch the JSON status of a pod."""
        command = f"kubectl get pod {pod_name} -n {namespace} -o json"
        return await self.call_kubectl(command)

    async def close(self):
        await self.client.aclose()


class MockMCPClient:
    """A mock MCP client for local development without a cluster."""
    async def fetch_pod_logs(self, namespace: str, pod_name: str) -> str:
        logger.info(f"Mock fetching logs for {namespace}/{pod_name}")
        return "ERROR: Failed to connect to database\\nTraceback (most recent call last):\\n  File \"app.py\", line 42, in connect\\nConnectionRefusedError: [Errno 111] Connection refused"

    async def fetch_pod_events(self, namespace: str, pod_name: str) -> str:
        logger.info(f"Mock fetching events for {namespace}/{pod_name}")
        return "1m  Warning  CrashLoopBackOff  pod/backend-service-abc123  Back-off restarting failed container"

    async def fetch_pod_status(self, namespace: str, pod_name: str) -> str:
        logger.info(f"Mock fetching status for {namespace}/{pod_name}")
        return '{"status": {"phase": "Running", "containerStatuses": [{"restartCount": 5}]}}'

    async def close(self):
        pass


# Instantiate the client based on environment
mcp: MCPClient | MockMCPClient
if os.environ.get("MCP_SERVER_URL"):
    mcp = MCPClient()
else:
    logger.warning("MCP_SERVER_URL not set, using MockMCPClient")
    mcp = MockMCPClient()
