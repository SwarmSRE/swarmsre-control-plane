from langchain_core.prompts import ChatPromptTemplate

LOG_HUNTER_SYSTEM_PROMPT = """You are an expert Kubernetes Site Reliability Engineer (SRE) specializing in log analysis.
Your job is to analyze raw pod logs and events to identify the root cause of an incident.
You must extract structured insights from the provided logs, including the error class, stack traces (if any), frequency, and when it was first seen.

If the logs do not contain clear errors, state that you could not find the issue and provide a low confidence score.
"""

log_hunter_prompt = ChatPromptTemplate.from_messages([
    ("system", LOG_HUNTER_SYSTEM_PROMPT),
    ("human", "Incident Reason: {reason}\nLogs: {logs}\nEvents: {events}")
])
