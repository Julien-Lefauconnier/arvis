# arvis/adapters/llm/contracts/usage.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LLMUsage:
    """
    Standardized usage information for any LLM provider.

    Designed to be:
    - provider-agnostic
    - serializable
    - cost-aware
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    # Optional cost (USD or internal unit)
    cost: float | None = None

    # Optional latency (ms)
    latency_ms: int | None = None

    # Provider metadata
    provider: str | None = None
    model: str | None = None

    def is_empty(self) -> bool:
        return self.total_tokens == 0

    def add(self, other: LLMUsage) -> LLMUsage:
        return LLMUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cost=(self.cost or 0.0) + (other.cost or 0.0)
            if self.cost is not None or other.cost is not None
            else None,
            latency_ms=(self.latency_ms or 0) + (other.latency_ms or 0)
            if self.latency_ms is not None or other.latency_ms is not None
            else None,
            provider=self.provider or other.provider,
            model=self.model or other.model,
        )
