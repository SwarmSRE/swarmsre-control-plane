"""Validate MCP client can connect and discover tools."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from core.mcp_client import mcp


async def main():
    try:
        session = await mcp._ensure_connected()
        print(f"Connected to MCP server at {mcp._base_url}")
        print(f"Available tools: {mcp._available_tools}")
        
        # Test call_kubectl
        result = await mcp.call_kubectl("kubectl get namespaces")
        print(f"\nkubectl get namespaces:\n{result}")
        
        # Test fetch_pod_events
        result = await mcp.fetch_pod_events("payment", "payment-service")
        print(f"\nPayment events:\n{result}")
        
        await mcp.close()
        print("\nAll MCP tests passed!")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    asyncio.run(main())
