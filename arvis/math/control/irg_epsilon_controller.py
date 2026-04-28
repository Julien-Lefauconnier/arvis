# arvis/math/control/irg_epsilon_controller.py

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from arvis.math.control.eps_adaptive import (
    CognitiveMode,
    EpsAdaptiveParams,
    adaptive_eps,
)
from arvis.math.core.normalization import clamp01
from arvis.math.signals import DriftSignal, RiskSignal, UncertaintySignal

# ============================================================
# IRG regime
# ============================================================


class IRGRegime(StrEnum):
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
        collapse_risk: RiskSignal,
        latent_volatility: DriftSignal,
    ) -> IRGRegime:
        # --- coercion (compat float)
        if not isinstance(collapse_risk, RiskSignal):
            collapse_risk = RiskSignal(collapse_risk)
        if not isinstance(latent_volatility, DriftSignal):
            latent_volatility = DriftSignal(latent_volatility)

        if collapse_risk.is_critical():
            return IRGRegime.COLLAPSE
        if collapse_risk.is_unstable_zone() or latent_volatility > 0.7:
            return IRGRegime.UNSTABLE
        if collapse_risk.is_transition_zone() or latent_volatility > 0.4:
            return IRGRegime.TRANSITION
        return IRGRegime.STABLE

    # ---------------------------------------------------------
    # structural modulation
    # ---------------------------------------------------------

    def structural_factor(
        self,
        regime: IRGRegime,
        collapse_risk: RiskSignal,
    ) -> float:
        p = self.irg_params

        # coercion
        if not isinstance(collapse_risk, RiskSignal):
            collapse_risk = RiskSignal(collapse_risk)

        r = collapse_risk.level()

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
        uncertainty: float | UncertaintySignal,
        budget_used: float,
        delta_v: float | DriftSignal,
        collapse_risk: float | RiskSignal,
        latent_volatility: float | DriftSignal,
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
        # Signal coercion (single entry point)
        # -----------------------------------------
        if not isinstance(uncertainty, UncertaintySignal):
            uncertainty = UncertaintySignal(uncertainty or 0.0)

        if not isinstance(collapse_risk, RiskSignal):
            collapse_risk = RiskSignal(collapse_risk or 0.0)

        if not isinstance(delta_v, DriftSignal):
            delta_v = DriftSignal(delta_v or 0.0)

        if not isinstance(latent_volatility, DriftSignal):
            latent_volatility = DriftSignal(latent_volatility or 0.0)

        # local epsilon
        eps_local = adaptive_eps(
            uncertainty=float(uncertainty),
            budget_used=budget_used,
            delta_v=float(delta_v),
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
