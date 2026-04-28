# arvis/adapters/llm/providers/mock.py

from __future__ import annotations

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
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
            metadata={
                "provider": "mock",
            },
        )
