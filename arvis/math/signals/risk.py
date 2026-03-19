# arvis/math/signals/risk.py

from __future__ import annotations

from dataclasses import dataclass
from arvis.math.signals.base import BaseSignal

from arvis.math.core.normalization import clamp01


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