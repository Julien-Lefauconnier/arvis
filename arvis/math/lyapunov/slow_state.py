# arvis/math/lyapunov/slow_state.py

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from arvis.reflexive.core.irg_latent_state import IRGLatentState


@dataclass(frozen=True)
class SlowState:
    """
    État lent z : IRG latent geometry (stability memory, structural risk, etc.).
    Immutable, numeric only, aligné sur IRGLatentState.
    """

    stability_memory: float = 0.0
    structural_risk: float = 0.0
    regime_persistence: float = 0.0
    uncertainty_drift: float = 0.0

    def as_vector(self) -> np.ndarray:
        return np.array(
            [
                self.stability_memory,
                self.structural_risk,
                self.regime_persistence,
                self.uncertainty_drift,
            ],
            dtype=float,
        )

    @classmethod
    def from_irg(cls, irg: IRGLatentState) -> SlowState:
        return cls(
            stability_memory=irg.stability_memory,
            structural_risk=irg.structural_risk,
            regime_persistence=irg.regime_persistence,
            uncertainty_drift=irg.uncertainty_drift,
        )

    @staticmethod
    def zero() -> SlowState:
        return SlowState(0.0, 0.0, 0.0, 0.0)
