from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.nodes.evaluate import evaluate_node
from agents.nodes.execute import execute_node
from agents.nodes.investigate import investigate_node
from agents.nodes.log_hunter import log_hunter_node
from agents.nodes.propose import propose_node
from agents.nodes.quarantine import quarantine_node
from agents.nodes.synthesize import synthesize_node
from agents.nodes.telemetry_analyst import telemetry_analyst_node
from agents.nodes.triage import triage_node
from agents.state import IncidentState


def should_quarantine(state: IncidentState) -> str:
    """Routing logic after triage."""
    if state.get("status") == "INVESTIGATING":
        return "quarantine"
    return END

# Build the graph
graph = StateGraph(IncidentState)

# Add nodes
graph.add_node("triage", triage_node)
graph.add_node("quarantine", quarantine_node)
graph.add_node("investigate", investigate_node)
graph.add_node("log_hunter", log_hunter_node)
graph.add_node("telemetry_analyst", telemetry_analyst_node)
graph.add_node("synthesize", synthesize_node)
graph.add_node("propose", propose_node)
graph.add_node("execute", execute_node)
graph.add_node("evaluate", evaluate_node)

def evaluate_route(state: IncidentState) -> str:
    """Route to propose if evaluate fails, else END."""
    if state.get("status") == "INVESTIGATING":
        return "propose"
    return END

# Add edges
graph.add_edge(START, "triage")
graph.add_conditional_edges("triage", should_quarantine)
graph.add_edge("quarantine", "investigate")
graph.add_edge("investigate", "log_hunter")
graph.add_edge("investigate", "telemetry_analyst")
graph.add_edge(["log_hunter", "telemetry_analyst"], "synthesize")
graph.add_edge("synthesize", "propose")
# HITL pause happens inside propose_node via interrupt()
graph.add_edge("propose", "execute")
graph.add_edge("execute", "evaluate")
graph.add_conditional_edges("evaluate", evaluate_route)

# Compile with checkpointer
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)
