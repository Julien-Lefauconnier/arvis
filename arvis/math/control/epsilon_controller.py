# arvis/math/control/epsilon_controller.py

import math
from dataclasses import dataclass


@dataclass
class EpsilonAdaptiveParams:
    eps_min: float = 1e-4
    eps_max: float = 1e-2
    sensitivity: float = 5.0


class AdaptiveEpsilonPolicy:
    """
    Continuous adaptive epsilon for Lyapunov contraction.
    """

    def __init__(self, params: EpsilonAdaptiveParams | None = None):
        self.params = params or EpsilonAdaptiveParams()

    def compute(self, collapse_risk: float | None) -> float:
        """
        collapse_risk ∈ [0, +inf)
        """
        if collapse_risk is None:
            return self.params.eps_max

        # exponential contraction
        eps = self.params.eps_min + (
            self.params.eps_max - self.params.eps_min
        ) * math.exp(-self.params.sensitivity * collapse_risk)

        # safety clamp
        return max(self.params.eps_min, min(self.params.eps_max, eps))


# backward compatibility
EpsilonAdaptiveController = AdaptiveEpsilonPolicy
