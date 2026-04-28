# arvis/cognition/control/exploration_snapshot.py
from __future__ import annotations

from dataclasses import dataclass

from arvis.math.core.normalization import clamp


@dataclass(frozen=True)
class ExplorationSnapshot:
    """
    Declarative exploration/exploitation configuration.

    Kernel invariants:
    - immutable
    - no execution logic
    - numeric only
    """

    exploration_factor: float
    confirmation_bias: float
    abstain_bias: float
    change_budget_scale: float
    rationale: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "exploration_factor", clamp(self.exploration_factor, 0.3, 1.5)
        )
        object.__setattr__(
            self, "confirmation_bias", clamp(self.confirmation_bias, 0.7, 2.0)
        )
        object.__setattr__(self, "abstain_bias", clamp(self.abstain_bias, 0.8, 2.0))
        object.__setattr__(
            self, "change_budget_scale", clamp(self.change_budget_scale, 0.5, 1.3)
        )
