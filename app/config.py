import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class Settings:
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = ""
    llm_timeout_seconds: float = 10
    max_workflows: int = 100
    max_task_length: int = 10_000
    max_output_length: int = 20_000
    max_steps: int = 6
    retry_limit: int = 1

    @property
    def demo_mode(self) -> bool:
        return not bool(self.llm_api_key and self.llm_model)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return Settings(
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        llm_model=os.getenv("LLM_MODEL", ""),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "10")),
    )
