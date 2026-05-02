# arvis/adapters/llm/providers/anthropic.py

from __future__ import annotations

from typing import Any

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.providers.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider using messages API.
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-latest",
        api_key: str | None = None,
    ) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ImportError(
                "AnthropicProvider requires `anthropic` package. "
                "Install with `pip install anthropic`."
            ) from exc

        self._client = Anthropic(api_key=api_key)
        self._model = model

    def generate(self, request: LLMRequest) -> LLMResponse:
        messages = [
            {
                "role": m.role,
                "content": m.content,
            }
            for m in (request.messages or [])
        ]

        response: Any = self._client.messages.create(
            model=request.effective_model or self._model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens or 1024,
        )

        parts = getattr(response, "content", [])
        text = "".join(getattr(part, "text", "") for part in parts)

        return LLMResponse(
            content=text,
            provider="anthropic",
            model=request.effective_model or self._model,
            metadata={
                "provider_response_id": getattr(response, "id", None),
            },
        )
