# arvis/adapters/llm/providers/ollama.py

from __future__ import annotations

from typing import Any

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.providers.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama provider.
    """

    def __init__(
        self,
        model: str = "llama3.1",
        host: str | None = None,
    ) -> None:
        try:
            import ollama
        except ImportError as exc:
            raise ImportError(
                "OllamaProvider requires `ollama` package. "
                "Install with `pip install ollama`."
            ) from exc

        self._client = ollama.Client(host=host) if host else ollama.Client()
        self._model = model

    def generate(self, request: LLMRequest) -> LLMResponse:
        messages = [
            {
                "role": m.role,
                "content": m.content,
            }
            for m in (request.messages or [])
        ]

        payload: dict[str, Any] = {
            "model": request.effective_model or self._model,
            "messages": messages,
            "options": {
                "temperature": request.temperature,
            },
        }

        response: Any = self._client.chat(**payload)

        content = response.get("message", {}).get("content", "")

        return LLMResponse(
            content=content,
            provider="ollama",
            model=request.effective_model or self._model,
            metadata={
                "provider_response_id": response.get("id"),
            },
        )
