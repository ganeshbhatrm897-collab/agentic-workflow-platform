import json
import urllib.error
import urllib.request

from app.config import Settings


class LLMService:
    """Small OpenAI-compatible client; callers must still validate generated data."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.llm_api_key and self.settings.llm_model)

    def complete(self, prompt: str) -> str:
        if not self.configured:
            raise RuntimeError("Optional LLM provider is not configured.")
        payload = json.dumps({
            "model": self.settings.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.settings.llm_timeout_seconds) as response:
                data = json.loads(response.read(100_000))
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, IndexError) as exc:
            raise RuntimeError("Optional LLM provider request failed.") from exc
