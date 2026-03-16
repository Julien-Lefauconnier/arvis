# arvis/math/lyapunov/lyapunov_gate.py

from enum import Enum
from dataclasses import dataclass, field

from arvis.math.lyapunov.lyapunov import LyapunovState, delta_V, V
from arvis.math.control.eps_adaptive import EpsAdaptiveParams, CognitiveMode, adaptive_eps
from arvis.math.core.normalization import clamp01


class LyapunovVerdict(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    ABSTAIN = "ABSTAIN"


@dataclass
class LyapunovGateParams:
    eps: float = 0.05
    abstain_threshold: float = 0.8

    eps_adaptive: EpsAdaptiveParams = field(default_factory=EpsAdaptiveParams)
    mode: CognitiveMode = CognitiveMode.NORMAL
    eps_override: float | None = None

    # ---- Stabilisation intégrale (Phase 1)
    # Damping: plus V est haut, plus on devient strict sur ΔV
    damping_gamma: float = 0.5   # 0 => off, >0 => stricter when V high

    # Extra penalty when ΔV is positive (instability growth)
    pos_dv_penalty: float = 0.25 # 0 => off


def lyapunov_gate(
    previous: LyapunovState,
    current: LyapunovState,
    params: LyapunovGateParams = LyapunovGateParams(),
) -> LyapunovVerdict:
    v = V(current)

    # --- global safety ---
    if v >= params.abstain_threshold:
        return LyapunovVerdict.ABSTAIN

    d = delta_V(previous, current)

    # External override has priority (multi-horizon controller)
    if params.eps_override is not None:
        eps_used = params.eps_override
    else:
        eps_used = adaptive_eps(
            uncertainty=current.uncertainty,
            budget_used=current.budget_used,
            delta_v=d,
            params=params.eps_adaptive,
            mode=params.mode,
            trust_score=0.0,
        )

    # -----------------------------
    # Stabilisation intégrale
    # -----------------------------
    # 1) damping: strict when V high
    gamma = max(0.0, float(params.damping_gamma))
    damping = 1.0 + gamma * clamp01(v)

    # reduce tolerance: eps_eff = eps_used / damping
    eps_eff = eps_used / damping

    # 2) penalize positive drift
    pen = max(0.0, float(params.pos_dv_penalty))
    d_eff = d + pen * clamp01(max(0.0, d))

    if d_eff > eps_eff:
        return LyapunovVerdict.REQUIRE_CONFIRMATION

    return LyapunovVerdict.ALLOW