# arvis/adapters/llm/providers/mock.py

from __future__ import annotations

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage
from arvis.adapters.llm.providers.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic provider for tests/dev.
    """

    def __init__(self, prefix: str = "mock") -> None:
        self._prefix = prefix

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=f"{self._prefix}:{request.prompt}",
            provider="mock",
            model="mock-model",
            usage=LLMUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            ),
            metadata={"provider": "mock"},
        )
