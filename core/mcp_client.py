"""
Production-grade MCP Client for SwarmSRE.

Connects to the Azure MCP Kubernetes server (ghcr.io/azure/mcp-kubernetes)
via the official MCP Python SDK using SSE transport.

Architecture:
  - Lazy-initialized: connection is established on first use, not at import.
  - Auto-reconnect: if the SSE session drops, the next call re-establishes it.
  - Tool discovery: on connect, we enumerate available tools and cache them.
  - Fail-fast: if MCP_SERVER_URL is unset, every call raises immediately.

The Azure MCP server exposes a unified `call_kubectl` tool that accepts
arbitrary kubectl commands. Our higher-level helpers (fetch_pod_logs, etc.)
build on top of that.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


class MCPClient:
    """Thread-safe, reconnecting MCP client over SSE transport."""

    def __init__(self) -> None:
        self._base_url: str | None = os.environ.get("MCP_SERVER_URL")
        if not self._base_url:
            raise ValueError(
                "MCP_SERVER_URL is required. Set it in your environment or .env file. "
                "Example: MCP_SERVER_URL=http://localhost:3000"
            )
        self._sse_url = f"{self._base_url.rstrip('/')}/sse"
        self._lock = asyncio.Lock()

        # Managed connection state
        self._session: ClientSession | None = None
        self._read_stream: Any = None
        self._write_stream: Any = None
        self._sse_cm: Any = None      # sse_client context manager
        self._session_cm: Any = None  # ClientSession context manager
        self._available_tools: list[str] = []
        self._connected = False

        logger.info(f"MCPClient configured for {self._base_url}")

    # ── Connection lifecycle ──────────────────────────────────────────

    async def _connect(self) -> None:
        """Establish SSE connection, initialize MCP session, discover tools."""
        if self._connected and self._session is not None:
            return

        # Tear down any stale state
        await self._disconnect()

        logger.info(f"Connecting to MCP server at {self._sse_url}")

        # Open the SSE transport
        self._sse_cm = sse_client(self._sse_url)
        self._read_stream, self._write_stream = await self._sse_cm.__aenter__()

        # Open the MCP session over the transport
        self._session_cm = ClientSession(self._read_stream, self._write_stream)
        self._session = await self._session_cm.__aenter__()

        # Protocol handshake
        await self._session.initialize()

        # Discover available tools
        tools_response = await self._session.list_tools()
        self._available_tools = [t.name for t in tools_response.tools]
        self._connected = True

        logger.info(
            f"MCP session established. Available tools: {self._available_tools}"
        )

    async def _disconnect(self) -> None:
        """Gracefully tear down session and transport."""
        self._connected = False
        self._session = None

        if self._session_cm is not None:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_cm = None

        if self._sse_cm is not None:
            try:
                await self._sse_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._sse_cm = None

    async def _ensure_connected(self) -> ClientSession:
        """Return a live session, reconnecting if necessary."""
        async with self._lock:
            if not self._connected or self._session is None:
                await self._connect()
            assert self._session is not None
            return self._session

    # ── Low-level tool call ───────────────────────────────────────────

    async def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """
        Call an MCP tool by name.

        Returns the text content of the first result, or the raw repr if
        the result has an unexpected shape.
        """
        session = await self._ensure_connected()

        logger.debug(f"Calling MCP tool '{tool_name}' with args: {arguments}")

        try:
            result = await session.call_tool(name=tool_name, arguments=arguments)
        except Exception as exc:
            # Connection died — mark as disconnected so next call reconnects
            logger.warning(f"MCP call failed ({exc}), will reconnect on next call")
            self._connected = False
            self._session = None
            raise

        # Extract text from MCP result content blocks
        if result.content:
            texts = [
                block.text
                for block in result.content
                if hasattr(block, "text")
            ]
            if texts:
                return "\n".join(texts)

        return str(result)

    # ── High-level kubectl helpers ────────────────────────────────────

    async def call_kubectl(self, command: str) -> str:
        """Execute an arbitrary kubectl command via the MCP server."""
        logger.info(f"MCP kubectl: {command}")
        return await self._call_tool("call_kubectl", {"command": command})

    async def fetch_pod_logs(self, namespace: str, pod_name: str) -> str:
        """Retrieve the last 100 lines of logs for a pod."""
        return await self.call_kubectl(
            f"kubectl logs {pod_name} -n {namespace} --tail=100"
        )

    async def fetch_pod_events(self, namespace: str, pod_name: str) -> str:
        """Retrieve Kubernetes events for a specific pod."""
        return await self.call_kubectl(
            f"kubectl get events -n {namespace} "
            f"--field-selector involvedObject.name={pod_name}"
        )

    async def fetch_pod_status(self, namespace: str, pod_name: str) -> str:
        """Retrieve full pod status as JSON."""
        return await self.call_kubectl(
            f"kubectl get pod {pod_name} -n {namespace} -o json"
        )

    async def fetch_pod_top(self, namespace: str, pod_name: str) -> str:
        """Retrieve resource usage metrics for a pod."""
        return await self.call_kubectl(
            f"kubectl top pod {pod_name} -n {namespace}"
        )

    async def quarantine_pod(self, namespace: str, pod_name: str, incident_id: str) -> str:
        """Quarantine a pod by relabeling its app label to isolate it from services."""
        # 1. Fetch current labels
        status_json = await self.fetch_pod_status(namespace, pod_name)
        import json
        try:
            pod_data = json.loads(status_json)
            labels = pod_data.get("metadata", {}).get("labels", {})
            app_label = labels.get("app")
            
            if not app_label:
                return "Failed: Pod does not have an 'app' label to quarantine."
                
            # 2. Apply new labels (overwrite app, add quarantine flags)
            new_app = f"{app_label}-quarantined"
            logger.info(f"Quarantining pod {namespace}/{pod_name}: changing app={app_label} to app={new_app}")
            
            # Use kubectl label with --overwrite
            cmd = (f"kubectl label pod {pod_name} -n {namespace} "
                   f"app={new_app} "
                   f"swarmsre.io/quarantined=true "
                   f"swarmsre.io/incident-id={incident_id} "
                   f"--overwrite")
            
            result = await self.call_kubectl(cmd)
            
            return json.dumps({
                "success": True,
                "original_app_label": app_label,
                "new_app_label": new_app,
                "pod_name": pod_name,
                "namespace": namespace,
                "kubectl_output": result
            })
        except Exception as e:
            logger.error(f"Failed to quarantine pod {pod_name}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    async def release_pod(self, namespace: str, pod_name: str, original_app_label: str) -> str:
        """Release a quarantined pod by restoring its original app label."""
        logger.info(f"Releasing pod {namespace}/{pod_name}: restoring app={original_app_label}")
        
        # Restore app label, remove quarantine flags
        cmd = (f"kubectl label pod {pod_name} -n {namespace} "
               f"app={original_app_label} "
               f"swarmsre.io/quarantined- "
               f"swarmsre.io/incident-id- "
               f"--overwrite")
               
        return await self.call_kubectl(cmd)

    async def apply_patch(self, patch_yaml: str) -> str:
        """Apply a YAML patch via kubectl apply."""
        logger.info("Applying patch via MCP kubectl apply")
        return await self._call_tool(
            "call_kubectl",
            {"command": f"kubectl apply -f - <<'EOF'\n{patch_yaml}\nEOF"},
        )

    # ── Lifecycle ─────────────────────────────────────────────────────

    async def close(self) -> None:
        """Shut down the MCP session and transport cleanly."""
        async with self._lock:
            await self._disconnect()
        logger.info("MCPClient closed")


# ── Singleton ─────────────────────────────────────────────────────────
# Lazy-initialized: the SSE connection is NOT opened at import time.
# The first call to any tool method triggers _ensure_connected().
mcp = MCPClient()
