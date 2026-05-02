# arvis/adapters/llm/providers/openai.py

from __future__ import annotations

from typing import Any

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.providers.base import BaseLLMProvider


class OpenAIAdapter(BaseLLMProvider):
    """
    Provider implementation for OpenAI Chat Completions.

    Kept intentionally lightweight and compatible with the legacy adapter API.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "OpenAIAdapter requires `openai` package. "
                "Install with `pip install openai`."
            ) from exc

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, request: LLMRequest) -> LLMResponse:
        messages: list[dict[str, str]] = [
            {
                "role": m.role,
                "content": m.content,
            }
            for m in (request.messages or [])
        ]

        response: Any = self._client.chat.completions.create(
            model=request.effective_model or self._model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        content = response.choices[0].message.content or ""

        return LLMResponse(
            content=content,
            provider="openai",
            model=request.effective_model or self._model,
            metadata={
                "provider_response_id": getattr(response, "id", None),
            },
        )
