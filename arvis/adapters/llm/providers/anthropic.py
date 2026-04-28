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
        response: Any = self._client.messages.create(
            model=request.model or self._model,
            system=request.system_prompt or "",
            messages=[
                {
                    "role": "user",
                    "content": request.prompt,
                }
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens or 1024,
        )

        parts = getattr(response, "content", [])
        text = "".join(getattr(part, "text", "") for part in parts)

        return LLMResponse(
            content=text,
            raw=response,
            metadata={
                "provider": "anthropic",
                "model": request.model or self._model,
            },
        )
