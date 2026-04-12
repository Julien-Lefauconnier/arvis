# arvis/kernel_core/process/budget.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CognitiveBudget:
    """
    Initial V1 budget dimensions.

    These are OS-level cognitive resources, not model/provider resources.
    """

    reasoning_steps: int = 1
    attention_tokens: int = 100
    uncertainty_budget: float = 1.0
    time_slice_ms: int = 50
    memory_span: int = 10

    def validate(self) -> None:
        if self.reasoning_steps < 0:
            raise ValueError("reasoning_steps must be >= 0")
        if self.attention_tokens < 0:
            raise ValueError("attention_tokens must be >= 0")
        if self.uncertainty_budget < 0.0:
            raise ValueError("uncertainty_budget must be >= 0")
        if self.time_slice_ms < 0:
            raise ValueError("time_slice_ms must be >= 0")
        if self.memory_span < 0:
            raise ValueError("memory_span must be >= 0")


@dataclass(frozen=True)
class BudgetConsumption:
    reasoning_steps: int = 0
    attention_tokens: int = 0
    uncertainty_spent: float = 0.0
    elapsed_ms: int = 0
    memory_span_used: int = 0

    def validate(self) -> None:
        if self.reasoning_steps < 0:
            raise ValueError("reasoning_steps must be >= 0")
        if self.attention_tokens < 0:
            raise ValueError("attention_tokens must be >= 0")
        if self.uncertainty_spent < 0.0:
            raise ValueError("uncertainty_spent must be >= 0")
        if self.elapsed_ms < 0:
            raise ValueError("elapsed_ms must be >= 0")
        if self.memory_span_used < 0:
            raise ValueError("memory_span_used must be >= 0")