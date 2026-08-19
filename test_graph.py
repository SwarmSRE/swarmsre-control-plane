import asyncio
from agents.graph import app as langgraph_app

async def main():
    initial_state = {
        "incident_id": "123",
        "status": "OPEN",
        "raw_event": {"reason": "CrashLoopBackOff"},
        "evidence": [],
        "messages": ["Incident created"]
    }
    config = {"configurable": {"thread_id": "123"}}
    try:
        print("Invoking graph...")
        result = await langgraph_app.ainvoke(initial_state, config)
        print("Graph finished", result)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
