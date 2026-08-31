# arvis/math/signals/risk.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.core.normalization import clamp01
from arvis.math.signals.base import BaseSignal


@dataclass(frozen=True)
class RiskSignal(BaseSignal):
    """
    Normalized collapse risk signal in [0,1].

    Invariants:
    - Always clamped to [0,1]
    - Immutable
    - Semantically distinct from other signals
    """

    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", clamp01(self.value))

    def __float__(self) -> float:
        return self.value

    # -----------------------------------------
    # Semantic helpers
    # -----------------------------------------
    # These descriptive bands (0.3 / 0.7 / 0.85) are OBSERVABILITY
    # vocabulary. They are deliberately distinct from the DECISION
    # thresholds of the input-risk gate (0.4 / 0.8, see
    # arvis/kernel/gate/input_risk.py): is_moderate() being True does
    # not imply the gate asks for confirmation, and is_high() does not
    # imply it refuses. Only the gate's constants gate (audit M7,
    # 2026-08).

    def level(self) -> float:
        return self.value

    def is_low(self) -> bool:
        return self.value < 0.3

    def is_moderate(self) -> bool:
        return 0.3 <= self.value < 0.7

    def is_high(self) -> bool:
        return self.value >= 0.7

    def is_critical(self) -> bool:
        return self.value >= 0.85

    def is_transition_zone(self) -> bool:
        return 0.3 <= self.value < 0.6

    def is_unstable_zone(self) -> bool:
        return 0.6 <= self.value < 0.85

    def __repr__(self) -> str:
        return f"RiskSignal(value={self.value:.4f})"
