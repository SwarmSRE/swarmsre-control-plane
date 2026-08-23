import os

import importlib
import os

from langchain_core.language_models.chat_models import BaseChatModel

PROVIDER_REGISTRY = {
    "google":    ("langchain_google_genai", "ChatGoogleGenerativeAI"),
    "openai":    ("langchain_openai",      "ChatOpenAI"),
    "anthropic": ("langchain_anthropic",   "ChatAnthropic"),
    "groq":      ("langchain_groq",        "ChatGroq"),
    "ollama":    ("langchain_ollama",       "ChatOllama"),
}

def _resolve_llm(provider: str, model: str, temperature: float = 0.0) -> BaseChatModel:
    """Dynamically import and instantiate the correct LangChain chat model."""
    provider = provider.lower()
    if provider not in PROVIDER_REGISTRY:
        raise ValueError(f"Unknown LLM provider '{provider}'. Supported: {list(PROVIDER_REGISTRY.keys())}")
    
    module_name, class_name = PROVIDER_REGISTRY[provider]
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        raise ImportError(f"Missing dependency for {provider}. Please run `uv pip install {module_name}`.")
    
    cls = getattr(module, class_name)
    return cls(model=model, temperature=temperature)

def get_orchestrator_llm(temperature: float = 0.0) -> BaseChatModel:
    """Returns the orchestrator LLM for complex reasoning and synthesis."""
    provider = os.getenv("ORCHESTRATOR_PROVIDER", "google")
    model = os.getenv("ORCHESTRATOR_MODEL", "gemini-3.6-flash")
    return _resolve_llm(provider, model, temperature)

def get_worker_llm(temperature: float = 0.0) -> BaseChatModel:
    """Returns a fast worker LLM for log/telemetry extraction."""
    provider = os.getenv("WORKER_PROVIDER", "groq")
    model = os.getenv("WORKER_MODEL", "openai/gpt-oss-120b")
    return _resolve_llm(provider, model, temperature)


