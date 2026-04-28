# arvis/math/control/eps_adaptive.py

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from arvis.math.core.normalization import clamp, clamp01


class CognitiveMode(StrEnum):
    NORMAL = "NORMAL"
    SAFE = "SAFE"
    CRITICAL = "CRITICAL"
    EXPLORATION = "EXPLORATION"


@dataclass(frozen=True)
class EpsAdaptiveParams:
    """
    Adaptive epsilon (drift tolerance) controller.

    All inputs are assumed normalized in [0,1].

    eps = base
          - a_u * uncertainty
          - a_b * budget_used
          - a_dv * max(0, delta_v)
          + a_trust * trust_score   (optional, default 0)
          then multiplied by mode factor (SAFE stricter),
          finally clamped to [eps_min, eps_max].
    """

    enabled: bool = False

    # Base / clamps
    base_eps: float = 0.05
    eps_min: float = 0.005
    eps_max: float = 0.20

    # Penalize instability (make eps smaller => more conservative)
    a_uncertainty: float = 0.04
    a_budget_used: float = 0.04
    a_pos_delta_v: float = 0.08

    # Optional "trust" knob (kept for phase B, default 0 => no effect)
    a_trust: float = 0.0

    # Mode multipliers
    safe_factor: float = 0.5
    critical_factor: float = 0.25
    exploration_factor: float = 1.2

    def clamped(self) -> EpsAdaptiveParams:
        # keep everything sane + deterministic
        return EpsAdaptiveParams(
            enabled=bool(self.enabled),
            base_eps=float(self.base_eps),
            eps_min=clamp(float(self.eps_min), 0.0, 1.0),
            eps_max=clamp(float(self.eps_max), 0.0, 1.0),
            a_uncertainty=max(0.0, float(self.a_uncertainty)),
            a_budget_used=max(0.0, float(self.a_budget_used)),
            a_pos_delta_v=max(0.0, float(self.a_pos_delta_v)),
            a_trust=max(0.0, float(self.a_trust)),
            safe_factor=clamp(float(self.safe_factor), 0.0, 2.0),
            exploration_factor=clamp(float(self.exploration_factor), 0.0, 3.0),
        )


def adaptive_eps(
    *,
    uncertainty: float,
    budget_used: float,
    delta_v: float,
    params: EpsAdaptiveParams,
    mode: CognitiveMode = CognitiveMode.NORMAL,
    trust_score: float = 0.0,
) -> float:
    """
    Compute an adaptive epsilon in [eps_min, eps_max].

    - uncertainty, budget_used in [0,1]
    - delta_v in [-1,1] (we only use max(0, delta_v))
    - trust_score in [0,1] (optional; default 0)
    """
    p = params.clamped()

    # If disabled, return base eps clamped to min/max
    if not p.enabled:
        return clamp(p.base_eps, p.eps_min, p.eps_max)

    u = clamp01(uncertainty)
    b = clamp01(budget_used)
    dv_pos = clamp01(max(0.0, float(delta_v)))
    t = clamp01(trust_score)

    eps = float(p.base_eps)
    eps -= p.a_uncertainty * u
    eps -= p.a_budget_used * b
    eps -= p.a_pos_delta_v * dv_pos
    eps += p.a_trust * t

    # Mode factor (SAFE stricter, EXPLORATION slightly looser)
    if mode == CognitiveMode.SAFE:
        eps *= p.safe_factor
    elif mode == CognitiveMode.CRITICAL:
        eps *= p.critical_factor
    elif mode == CognitiveMode.EXPLORATION:
        eps *= p.exploration_factor

    # Final clamp
    return clamp(eps, p.eps_min, p.eps_max)
