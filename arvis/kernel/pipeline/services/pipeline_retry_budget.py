# arvis/kernel/pipeline/services/pipeline_retry_budget.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PipelineRetryBudgetDecision:
    allowed: bool
    reason: str
    remaining: int


@dataclass(slots=True)
class PipelineRetryBudget:
    max_retries: int

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

    def decide(self, *, consumed_retries: int) -> PipelineRetryBudgetDecision:
        if consumed_retries < 0:
            raise ValueError("consumed_retries must be >= 0")

        remaining = self.max_retries - consumed_retries

        if remaining <= 0:
            return PipelineRetryBudgetDecision(
                allowed=False,
                reason="retry_budget_exhausted",
                remaining=0,
            )

        return PipelineRetryBudgetDecision(
            allowed=True,
            reason="retry_budget_available",
            remaining=remaining,
        )
