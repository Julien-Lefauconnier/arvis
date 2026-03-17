# arvis/math/control/irg_epsilon_controller.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from arvis.math.control.eps_adaptive import adaptive_eps, EpsAdaptiveParams, CognitiveMode
from arvis.math.core.normalization import clamp01
from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal
from arvis.math.signals.utils import signal_value


# ============================================================
# IRG regime
# ============================================================


class IRGRegime(str, Enum):
    STABLE = "STABLE"
    TRANSITION = "TRANSITION"
    UNSTABLE = "UNSTABLE"
    COLLAPSE = "COLLAPSE"


# ============================================================
# Params
# ============================================================


@dataclass(frozen=True)
class IRGEpsilonParams:
    """
    Structure-aware epsilon controller.

    Modulates the local adaptive epsilon using:
    - structural collapse risk
    - latent volatility
    - regime blending
    """

    enabled: bool = True

    # structural sensitivity
    k_structural: float = 2.5

    # regime gains
    stable_boost: float = 1.3
    transition_gain: float = 1.0
    unstable_penalty: float = 0.7
    collapse_penalty: float = 0.4

    # smoothing inertia
    smoothing: float = 0.2


# ============================================================
# Controller
# ============================================================


class IRGEpsilonController:
    """
    Combines local adaptive epsilon with global IRG structural awareness.

    ZKCS safe:
    - no exposure of regime or structural risk.
    """

    def __init__(
        self,
        adaptive_params: EpsAdaptiveParams,
        irg_params: IRGEpsilonParams | None = None,
    ):
        self.adaptive_params = adaptive_params
        self.irg_params = irg_params or IRGEpsilonParams()
        self._last_eps: float | None = None

    # ---------------------------------------------------------
    # regime detection
    # ---------------------------------------------------------

    def infer_regime(
        self,
        collapse_risk: float,
        latent_volatility: float,
    ) -> IRGRegime:
        cr = collapse_risk
        lv = latent_volatility

        r = signal_value(cr)
        v = signal_value(lv)

        if hasattr(cr, "is_critical") and cr.is_critical():
            return IRGRegime.COLLAPSE
        if (hasattr(cr, "is_unstable_zone") and cr.is_unstable_zone()) or v > 0.7:
            return IRGRegime.UNSTABLE
        if (hasattr(cr, "is_transition_zone") and cr.is_transition_zone()) or v > 0.4:
            return IRGRegime.TRANSITION
        return IRGRegime.STABLE

    # ---------------------------------------------------------
    # structural modulation
    # ---------------------------------------------------------

    def structural_factor(
        self,
        regime: IRGRegime,
        collapse_risk: float,
    ) -> float:
        p = self.irg_params
       
        r = signal_value(collapse_risk)

        base = math.exp(-p.k_structural * r)

        if regime == IRGRegime.STABLE:
            return base * p.stable_boost
        if regime == IRGRegime.TRANSITION:
            return base * p.transition_gain
        if regime == IRGRegime.UNSTABLE:
            return base * p.unstable_penalty
        return base * p.collapse_penalty

    # ---------------------------------------------------------
    # main API
    # ---------------------------------------------------------

    def compute(
        self,
        *,
        uncertainty: float,
        budget_used: float,
        delta_v: float,
        collapse_risk: float,
        latent_volatility: float,
        mode: CognitiveMode,
        trust_score: float = 0.0,
    ) -> float:
        """
        Final epsilon.

        1. local adaptive epsilon
        2. structural modulation
        3. smoothing inertia
        """
        # -----------------------------------------
        # Signal-safe normalization
        # -----------------------------------------
        uncertainty = signal_value(uncertainty, 0.0)
        collapse_risk = signal_value(collapse_risk, 0.0)
        delta_v = signal_value(delta_v, 0.0)

        # local epsilon
        eps_local = adaptive_eps(
            uncertainty=uncertainty,
            budget_used=budget_used,
            delta_v=delta_v,
            params=self.adaptive_params,
            mode=mode,
            trust_score=trust_score,
        )

        if not self.irg_params.enabled:
            return eps_local

        regime = self.infer_regime(
            collapse_risk=collapse_risk,
            latent_volatility=latent_volatility,
        )

        factor = self.structural_factor(
            regime=regime,
            collapse_risk=collapse_risk,
        )

        eps = eps_local * factor

        # smoothing
        if self._last_eps is not None:
            s = clamp01(self.irg_params.smoothing)
            eps = (1 - s) * eps + s * self._last_eps

        self._last_eps = eps
        return eps