from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock").strip().lower()
    llm_model: str = os.getenv("LLM_MODEL", "").strip()
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    search_provider: str = os.getenv("SEARCH_PROVIDER", "auto").strip().lower()
    max_reflection_loops: int = int(os.getenv("MAX_REFLECTION_LOOPS", "2"))
    max_research_steps: int = int(os.getenv("MAX_RESEARCH_STEPS", "5"))
    require_human_approval: bool = os.getenv("REQUIRE_HUMAN_APPROVAL", "false").lower() in {"1", "true", "yes"}
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

settings = Settings()
