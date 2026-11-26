"""Search adapter with Tavily and DuckDuckGo alternatives."""
from __future__ import annotations
import os


def search_web(query: str, max_results: int = 5) -> list[dict]:
    provider = os.getenv("SEARCH_PROVIDER", "auto").lower()
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if provider == "auto":
        provider = "tavily" if key else "duckduckgo"
    if provider == "tavily":
        if not key:
            raise RuntimeError("SEARCH_PROVIDER=tavily requires TAVILY_API_KEY. Use duckduckgo or auto instead.")
        from tavily import TavilyClient
        response = TavilyClient(api_key=key).search(query=query, max_results=max_results)
        return [{"title": x.get("title", "Untitled"), "url": x.get("url", ""),
                 "content": x.get("content", ""), "source": "Tavily"}
                for x in response.get("results", [])]
    if provider == "duckduckgo":
        from ddgs import DDGS
        with DDGS() as ddgs:
            rows = list(ddgs.text(query, max_results=max_results))
        return [{"title": x.get("title", "Untitled"), "url": x.get("href", ""),
                 "content": x.get("body", ""), "source": "DuckDuckGo"} for x in rows]
    raise ValueError(f"Unsupported SEARCH_PROVIDER: {provider}")
