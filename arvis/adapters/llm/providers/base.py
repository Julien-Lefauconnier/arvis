# arvis/adapters/llm/providers/base.py

from __future__ import annotations

from abc import ABC, abstractmethod

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from a governed request."""
        raise NotImplementedError
