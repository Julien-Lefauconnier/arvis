# arvis/cognition/control/adaptive_mode_snapshot.py
from __future__ import annotations

from dataclasses import dataclass

from arvis.math.core.normalization import clamp01


@dataclass(frozen=True)
class AdaptiveModeSnapshot:
    """
    Declarative adaptive cognition mode.

    Kernel invariants:
    - immutable
    - no dynamic evaluation
    """

    risk: float
    mode: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk", clamp01(self.risk))
