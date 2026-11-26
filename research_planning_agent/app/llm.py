"""LLM adapter. Mock mode makes the complete workflow runnable without API credentials."""
from __future__ import annotations
import json
from typing import Any
from app.config import settings

class MockChatModel:
    def invoke(self, prompt: Any) -> str:
        text = str(prompt)
        if "Return ONLY a JSON array" in text:
            topic = text.split("USER REQUEST:", 1)[-1].strip()[:120]
            return json.dumps([
                {"title": f"Background and context: {topic}", "query": f"{topic} overview background"},
                {"title": f"Evidence, data and current state: {topic}", "query": f"{topic} data statistics evidence"},
                {"title": f"Options, risks and practical considerations: {topic}", "query": f"{topic} options risks challenges"},
                {"title": f"Recommendations and implementation: {topic}", "query": f"{topic} recommendations implementation roadmap"},
            ])
        if "Return ONLY JSON" in text:
            return json.dumps({"needs_more_research": False, "gaps": []})
        return (
            "## Executive summary\n\n"
            "This draft was generated in MOCK mode. Configure a real LLM provider for deeper synthesis. "
            "The evidence section below contains the retrieved source snippets; verify important claims before acting.\n\n"
            + text[-9000:]
        )


def get_chat_model():
    provider = settings.llm_provider
    if provider == "mock":
        return MockChatModel()
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.llm_model or "llama3.1", base_url=settings.ollama_base_url,
                          temperature=settings.llm_temperature)
    from langchain.chat_models import init_chat_model
    model_names = {"openai": settings.llm_model or "gpt-4o-mini",
                   "anthropic": settings.llm_model or "claude-3-5-haiku-latest",
                   "google_genai": settings.llm_model or "gemini-2.0-flash"}
    if provider not in model_names:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
    return init_chat_model(model_names[provider], model_provider=provider,
                           temperature=settings.llm_temperature)


def invoke_text(model, prompt: str) -> str:
    result = model.invoke(prompt)
    content = getattr(result, "content", result)
    if isinstance(content, list):
        return "\n".join(str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in content)
    return str(content)
