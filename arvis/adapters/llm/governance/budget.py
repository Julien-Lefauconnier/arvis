# arvis/adapters/llm/governance/budget.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LLMBudget:
    """
    Represents a budget constraint for an LLM call.

    This is intentionally simple and composable.
    """

    max_tokens: int | None = None
    max_cost: float | None = None  # USD or internal unit

    def allows_tokens(self, tokens: int) -> bool:
        if self.max_tokens is None:
            return True
        return tokens <= self.max_tokens

    def allows_cost(self, cost: float) -> bool:
        if self.max_cost is None:
            return True
        return cost <= self.max_cost

    def is_within(self, tokens: int, cost: float | None) -> bool:
        if not self.allows_tokens(tokens):
            return False

        if cost is not None and not self.allows_cost(cost):
            return False

        return True
