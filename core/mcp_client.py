import asyncio
import logging
import os
import shutil
from typing import Any

import httpx

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self):
        self.base_url = os.environ.get("MCP_SERVER_URL", "http://localhost:3000")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict[str, Any]:
        try:
            response = await self.client.post(
                f"/tools/{tool_name}/execute",
                json={"arguments": arguments}
            )
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.debug(f"MCP server unavailable ({e}), falling back to direct kubectl")
            return {"error": str(e), "status": "failed"}

    async def call_kubectl(self, command: str) -> str:
        logger.info(f"Calling MCP kubectl: {command}")
        result = await self._call_tool("call_kubectl", {"command": command})
        if result.get("status") == "failed":
            # Fallback to direct kubectl execution
            parts = command.split()
            if parts and parts[0] == "kubectl":
                parts = parts[1:]
            return await DirectKubectlClient()._run(parts)
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
            logger.info("MCP server unavailable for apply_patch, using DirectKubectlClient")
            return await DirectKubectlClient().apply_patch(patch_yaml)
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0].get("text", "")
        return str(result)

    async def close(self):
        await self.client.aclose()


class DirectKubectlClient:
    """Directly interacts with the Kubernetes cluster via local kubectl CLI."""

    async def _run(self, args: list[str]) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                "kubectl", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                err = stderr.decode().strip()
                logger.warning(f"kubectl {' '.join(args)} failed: {err}")
                return err
            return stdout.decode().strip()
        except Exception as e:
            logger.error(f"Failed to execute kubectl: {e}")
            return f"Error executing kubectl: {e}"

    async def fetch_pod_logs(self, namespace: str, pod_name: str) -> str:
        return await self._run(["logs", pod_name, "-n", namespace, "--tail=100"])

    async def fetch_pod_events(self, namespace: str, pod_name: str) -> str:
        return await self._run(["get", "events", "-n", namespace, f"--field-selector=involvedObject.name={pod_name}"])

    async def fetch_pod_status(self, namespace: str, pod_name: str) -> str:
        return await self._run(["get", "pod", pod_name, "-n", namespace, "-o", "json"])

    async def fetch_pod_top(self, namespace: str, pod_name: str) -> str:
        return await self._run(["top", "pod", pod_name, "-n", namespace])

    async def apply_patch(self, patch_yaml: str) -> str:
        try:
            # Check if this is a complete manifest with kind & apiVersion
            if "apiVersion:" in patch_yaml and "kind:" in patch_yaml:
                proc = await asyncio.create_subprocess_exec(
                    "kubectl", "apply", "-f", "-",
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate(input=patch_yaml.encode())
                if proc.returncode == 0:
                    return stdout.decode().strip()
                return stderr.decode().strip()
            else:
                # Strategic merge patch on payment-service deployment in demo namespace
                proc = await asyncio.create_subprocess_exec(
                    "kubectl", "patch", "deployment", "payment-service", "-n", "demo",
                    "--patch", patch_yaml,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0:
                    return stdout.decode().strip()
                return stderr.decode().strip()
        except Exception as e:
            logger.error(f"Failed to apply patch via kubectl: {e}")
            return f"Failed to apply patch: {e}"

    async def close(self):
        pass


class MockMCPClient:
    """Mock MCP client for fallback."""
    async def fetch_pod_logs(self, namespace: str, pod_name: str) -> str:
        return "ERROR: Failed to connect to database\nConnectionRefusedError: [Errno 111] Connection refused"

    async def fetch_pod_events(self, namespace: str, pod_name: str) -> str:
        return f"1m  Warning  ImagePullBackOff  pod/{pod_name}  Error: ImagePullBackOff"

    async def fetch_pod_status(self, namespace: str, pod_name: str) -> str:
        return '{"status": {"phase": "Running", "containerStatuses": [{"restartCount": 5}]}}'

    async def fetch_pod_top(self, namespace: str, pod_name: str) -> str:
        return f"NAME                          CPU(cores)   MEMORY(bytes)\n{pod_name}        1500m        1024Mi"

    async def apply_patch(self, patch_yaml: str) -> str:
        return "resource patched successfully"

    async def close(self):
        pass


# Instantiate the client based on environment
mcp: MCPClient | DirectKubectlClient | MockMCPClient
if os.environ.get("MCP_SERVER_URL"):
    mcp = MCPClient()
elif shutil.which("kubectl"):
    logger.info("Using DirectKubectlClient for live Kubernetes cluster interaction")
    mcp = DirectKubectlClient()
else:
    logger.warning("kubectl not found and MCP_SERVER_URL not set, using MockMCPClient")
    mcp = MockMCPClient()

