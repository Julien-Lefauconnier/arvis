# arvis/cognition/control/regime_control_snapshot.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.core.normalization import clamp


@dataclass(frozen=True)
class RegimeControlSnapshot:
    """
    Declarative mapping of regime → control behavior.

    Kernel invariants:
    - immutable
    - no policy logic
    """

    mode: str
    exploration_factor: float
    confirmation_bias: float
    epsilon_multiplier: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "exploration_factor", clamp(self.exploration_factor, 0.3, 1.5)
        )
        object.__setattr__(
            self, "confirmation_bias", clamp(self.confirmation_bias, 0.7, 2.0)
        )
        object.__setattr__(
            self, "epsilon_multiplier", max(0.0, float(self.epsilon_multiplier))
        )
