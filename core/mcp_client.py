import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self):
        self.base_url = os.environ.get("MCP_SERVER_URL")
        if not self.base_url:
            raise ValueError(
                "MCP_SERVER_URL is required. Set it in your environment or .env file. "
                "Example: MCP_SERVER_URL=http://localhost:3000"
            )
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        logger.info(f"Initialized MCPClient with base URL: {self.base_url}")

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict[str, Any]:
        """Calls an MCP tool and raises exceptions on failure."""
        logger.debug(f"Calling MCP tool {tool_name} with args: {arguments}")
        response = await self.client.post(
            f"/tools/{tool_name}/execute",
            json={"arguments": arguments}
        )
        response.raise_for_status()
        return response.json()

    async def call_kubectl(self, command: str) -> str:
        logger.info(f"Calling MCP kubectl: {command}")
        result = await self._call_tool("call_kubectl", {"command": command})
        
        if result.get("status") == "failed":
            raise RuntimeError(f"MCP server failed to execute kubectl: {result.get('error')}")
            
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0].get("text", "")
        return str(result)


    async def fetch_pod_logs(self, namespace: str, pod_name: str) -> str:
        command = f"kubectl logs {pod_name} -n {namespace} --tail=100"
        return await self.call_kubectl(command)

    async def fetch_pod_events(self, namespace: str, pod_name: str) -> str:
        command = f"kubectl get events -n {namespace} --field-selector involvedObject.name={pod_name}"
        return await self.call_kubectl(command)

    async def fetch_pod_status(self, namespace: str, pod_name: str) -> str:
        command = f"kubectl get pod {pod_name} -n {namespace} -o json"
        return await self.call_kubectl(command)

    async def fetch_pod_top(self, namespace: str, pod_name: str) -> str:
        command = f"kubectl top pod {pod_name} -n {namespace}"
        return await self.call_kubectl(command)

    async def apply_patch(self, patch_yaml: str) -> str:
        logger.info("Calling MCP kubectl apply")
        result = await self._call_tool("apply_patch", {"yaml": patch_yaml})
        
        if result.get("status") == "failed":
            raise RuntimeError(f"MCP server failed to apply patch: {result.get('error')}")
            
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0].get("text", "")
        return str(result)

    async def close(self):
        await self.client.aclose()


# Instantiate the singleton client
# This will crash fast if MCP_SERVER_URL is missing, enforcing our architecture.
mcp = MCPClient()
