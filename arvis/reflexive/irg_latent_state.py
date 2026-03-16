# arvis/reflexive/irg_latent_state.py

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class IRGLatentState:
    """
    Reflexive latent geometry representation.

    Kernel guarantees:
    - numeric only
    - immutable
    """

    stability_memory: float = 0.0
    structural_risk: float = 0.0
    regime_persistence: float = 0.0
    uncertainty_drift: float = 0.0

    def as_vector(self) -> Tuple[float, float, float, float]:
        return (
            self.stability_memory,
            self.structural_risk,
            self.regime_persistence,
            self.uncertainty_drift,
        )