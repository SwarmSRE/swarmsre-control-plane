from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import IncidentState
from agents.nodes.triage import triage_node
from agents.nodes.investigate import investigate_node
from agents.nodes.synthesize import synthesize_node
from agents.nodes.propose import propose_node
from agents.nodes.execute import execute_node
from agents.nodes.evaluate import evaluate_node

def should_investigate(state: IncidentState) -> str:
    """Routing logic after triage."""
    if state.get("status") == "INVESTIGATING":
        return "investigate"
    return END

# Build the graph
graph = StateGraph(IncidentState)

# Add nodes
graph.add_node("triage", triage_node)
graph.add_node("investigate", investigate_node)
graph.add_node("synthesize", synthesize_node)
graph.add_node("propose", propose_node)
graph.add_node("execute", execute_node)
graph.add_node("evaluate", evaluate_node)

# Add edges
graph.add_edge(START, "triage")
graph.add_conditional_edges("triage", should_investigate)
graph.add_edge("investigate", "synthesize")
graph.add_edge("synthesize", "propose")
# HITL pause happens inside propose_node via interrupt()
graph.add_edge("propose", "execute")
graph.add_edge("execute", "evaluate")
graph.add_edge("evaluate", END)

# Compile with checkpointer
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)
