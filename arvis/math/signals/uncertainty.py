# arvis/math/signals/uncertainty.py

from __future__ import annotations

from dataclasses import dataclass
from arvis.math.signals.base import BaseSignal

from arvis.math.core.normalization import clamp01


@dataclass(frozen=True)
class UncertaintySignal(BaseSignal):
    """
    Normalized uncertainty signal in [0,1].
    """

    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", clamp01(self.value))

    def __float__(self) -> float:
        return self.value

    def level(self) -> float:
        return self.value

    def is_high(self) -> bool:
        return self.value >= 0.7

    def __repr__(self) -> str:
        return f"UncertaintySignal(value={self.value:.4f})"
