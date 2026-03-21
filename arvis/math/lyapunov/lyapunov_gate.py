# arvis/math/lyapunov/lyapunov_gate.py

from enum import Enum
from dataclasses import dataclass, field

from arvis.math.lyapunov.lyapunov import LyapunovState, delta_V, V
from arvis.math.control.eps_adaptive import EpsAdaptiveParams, CognitiveMode, adaptive_eps
from arvis.math.core.normalization import clamp01
from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState
from .slow_state import SlowState


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


def lyapunov_gate(  # noqa: C901
    previous: LyapunovState,
    current: LyapunovState,
    params: LyapunovGateParams = LyapunovGateParams(),
    prev_slow: SlowState | None = None,
    current_slow: SlowState | None = None,
    prev_symbolic: SymbolicState | None = None,
    current_symbolic: SymbolicState | None = None,
) -> LyapunovVerdict:
    # Local fast Lyapunov gate only.
    # Composite / temporal policy is handled upstream in gate_stage.
    if isinstance(current, float):
        current = LyapunovState.from_scalar(current)
    if isinstance(previous, float):
        previous = LyapunovState.from_scalar(previous)
    if previous is None or current is None:
        return LyapunovVerdict.REQUIRE_CONFIRMATION

    v = V(current)

    # Global safety on instantaneous fast energy
    if v >= params.abstain_threshold:
        return LyapunovVerdict.ABSTAIN

    d = delta_V(previous, current)

    # External override has priority
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


    # 1) damping: stricter when V is high
    gamma = max(0.0, float(params.damping_gamma))
    damping = 1.0 + gamma * clamp01(v)

    eps_eff = eps_used / damping

    # 2) penalize positive ΔV
    pen = max(0.0, float(params.pos_dv_penalty))
    d_eff = d + pen * clamp01(max(0.0, d))

    if d_eff > eps_eff:
        return LyapunovVerdict.REQUIRE_CONFIRMATION

    return LyapunovVerdict.ALLOW