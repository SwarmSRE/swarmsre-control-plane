import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


def get_orchestrator_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """Returns the orchestrator LLM (Gemini) for complex reasoning and synthesis."""
    model = os.getenv("ORCHESTRATOR_MODEL", "gemini-3.6-flash")
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
    )

def get_worker_llm(temperature: float = 0.0) -> ChatGroq:
    """Returns a fast worker LLM (Groq) for log/telemetry extraction."""
    model = os.getenv("WORKER_MODEL", "openai/gpt-oss-120b")
    return ChatGroq(
        model=model,
        temperature=temperature,
    )


