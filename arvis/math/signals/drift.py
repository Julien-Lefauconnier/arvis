# arvis/math/signals/drift.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.core.normalization import clamp01


@dataclass(frozen=True)
class DriftSignal:
    """
    Normalized drift signal in [0,1].

    Note:
    Drift is often signed in theory, but here we normalize
    its magnitude into [0,1] for stability control usage.
    """
    value: float

    def __post_init__(self):
        object.__setattr__(self, "value", clamp01(abs(self.value)))

    def __float__(self) -> float:
        return self.value
    
    def level(self) -> float:
        return self.value

    def is_high(self) -> bool:
        return self.value >= 0.7

    def __repr__(self) -> str:
        return f"DriftSignal(value={self.value:.4f})"