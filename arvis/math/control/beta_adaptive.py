# arvis/math/control/beta_adaptive.py

from dataclasses import dataclass
from typing import Optional

from arvis.math.stability.regime_estimator import RegimeSnapshot


@dataclass
class BetaAdaptiveParams:
    beta_min: float = 1.0
    beta_max: float = 5.0


class BetaAdaptiveController:
    """
    Adaptive confidence parameter for probabilistic Lyapunov.

    Deterministic and explainable.
    """

    def __init__(self, params: Optional[BetaAdaptiveParams] = None):
        self.params = params or BetaAdaptiveParams()

    def compute(
        self,
        regime: Optional[RegimeSnapshot],
        variance: float,
        drift: float,
    ) -> float:
        # base
        beta = self.params.beta_min

        # -------------------
        # regime-based boost
        # -------------------
        if regime:
            if regime.regime == "stable":
                beta += 0.5
            elif regime.regime == "oscillatory":
                beta += 1.0
            elif regime.regime == "critical":
                beta += 2.0
            elif regime.regime == "chaotic":
                beta += 3.0
            elif regime.regime == "transition":
                beta += 1.5

        # -------------------
        # variance awareness
        # -------------------
        beta += 2.0 * variance

        # -------------------
        # drift awareness
        # -------------------
        beta += 2.0 * drift

        # clamp
        return max(self.params.beta_min, min(self.params.beta_max, beta))
