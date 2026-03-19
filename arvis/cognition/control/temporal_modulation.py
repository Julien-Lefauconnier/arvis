# arvis/cognition/control/temporal_modulation.py
from __future__ import annotations

from dataclasses import dataclass
from arvis.math.core.normalization import clamp01

@dataclass(frozen=True)
class TemporalModulation:
    """
    Temporal modulation factors.

    Kernel invariants:
    - no timeline access
    - no computation
    - purely declarative multipliers
    """

    risk_multiplier: float = 1.0
    epsilon_multiplier: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_multiplier", max(0.0, float(self.risk_multiplier)))
        object.__setattr__(self, "epsilon_multiplier", clamp01(self.epsilon_multiplier) if self.epsilon_multiplier <= 1.0 else float(self.epsilon_multiplier))