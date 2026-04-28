# arvis/adapters/llm/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse


class BaseLLMAdapter(ABC):
    """
    Backward-compatible LLM adapter interface.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str | LLMRequest,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        raise NotImplementedError


__all__ = [
    "BaseLLMAdapter",
    "LLMRequest",
    "LLMResponse",
]
