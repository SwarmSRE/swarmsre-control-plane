import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


def get_orchestrator_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Returns the orchestrator LLM (Gemini) for complex reasoning and synthesis."""
    # Use gemini-1.5-pro or similar model
    model = os.getenv("ORCHESTRATOR_MODEL", "gemini-1.5-pro")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
    )

def get_worker_llm(temperature: float = 0.0) -> ChatGroq:
    """Returns a fast worker LLM (Groq) for log/telemetry extraction."""
    # Use llama3-8b-8192 or llama3-70b-8192 for fast structured extraction
    model = os.getenv("WORKER_MODEL", "llama3-70b-8192")
    return ChatGroq(
        model=model,
        temperature=temperature,
    )
