# arvis/adapters/llm/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LLMResponse:
    def __init__(
        self,
        content: str,
        raw: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.raw = raw
        self.metadata = metadata or {}


class BaseLLMAdapter(ABC):
    """
    Standard interface for all LLM providers.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate text from prompt.
        """
        pass