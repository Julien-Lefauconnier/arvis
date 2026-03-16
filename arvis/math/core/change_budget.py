# arvis/math/core/change_budget.py

from __future__ import annotations

from dataclasses import dataclass

from .normalization import clamp01


@dataclass(frozen=True)
class ChangeBudget:
    """
    Tracks drift consumption under a fixed budget B in [0,1].

    consumption is monotone non-decreasing (clamped).
    """
    budget: float
    consumption: float = 0.0

    def __post_init__(self):
        object.__setattr__(self, "budget", clamp01(self.budget))
        object.__setattr__(self, "consumption", clamp01(self.consumption))

    @property
    def remaining(self) -> float:
        return clamp01(self.budget - self.consumption)

    @property
    def exhausted(self) -> bool:
        # exhausted means no remaining margin
        return self.remaining <= 0.0

    def can_consume(self, drift: float) -> bool:
        drift = clamp01(drift)
        return (self.consumption + drift) <= self.budget + 1e-12

    def consume(self, drift: float) -> "ChangeBudget":
        drift = clamp01(drift)
        return ChangeBudget(
            budget=self.budget,
            consumption=clamp01(self.consumption + drift),
        )