from langchain_core.prompts import ChatPromptTemplate

TELEMETRY_ANALYST_SYSTEM_PROMPT = """You are an expert Kubernetes Site Reliability Engineer (SRE) specializing in telemetry and resource analysis.
Your job is to analyze the provided pod telemetry, status conditions, and events to identify resource saturation, anomalies, or capacity constraints.
You must extract structured insights from the provided data, classifying the resource status and identifying any saturation signals.

If the telemetry shows normal operation, classify it as "healthy".
"""

telemetry_analyst_prompt = ChatPromptTemplate.from_messages([
    ("system", TELEMETRY_ANALYST_SYSTEM_PROMPT),
    ("human", "Incident Reason: {reason}\nTelemetry/Status: {telemetry}\nEvents: {events}")
])
