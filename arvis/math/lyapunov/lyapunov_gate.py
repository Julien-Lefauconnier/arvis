# arvis/math/lyapunov/lyapunov_gate.py

from dataclasses import dataclass, field
from enum import StrEnum

from arvis.math.control.eps_adaptive import (
    CognitiveMode,
    EpsAdaptiveParams,
    adaptive_eps,
)
from arvis.math.core.normalization import clamp01
from arvis.math.lyapunov.lyapunov import LyapunovState, V, delta_V
from arvis.math.state.symbolic_state import SymbolicState

from .slow_state import SlowState


class LyapunovVerdict(StrEnum):
    ALLOW = "ALLOW"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    ABSTAIN = "ABSTAIN"


@dataclass
class LyapunovGateParams:
    eps: float = 0.05
    abstain_threshold: float = 0.8
    # Worst-axis guard (decision DM3, campaign MATH-A M4). V is a
    # convex mean, so a single saturated axis is diluted by a factor of
    # four: risk=1.0 alone gives V=0.25 and the mean threshold never
    # refuses (audit M3). A single axis at or above this level refuses
    # outright, whatever the mean says. Strictly monotone hardening;
    # 0.95 means "essentially saturated", tunable per host.
    axis_abstain_threshold: float = 0.95

    eps_adaptive: EpsAdaptiveParams = field(default_factory=EpsAdaptiveParams)
    mode: CognitiveMode = CognitiveMode.NORMAL
    eps_override: float | None = None

    # ---- Integral stabilization (Phase 1)
    # Damping: plus V est haut, plus on devient strict sur ΔV
    damping_gamma: float = 0.5  # 0 => off, >0 => stricter when V high

    # Extra penalty when ΔV is positive (instability growth)
    pos_dv_penalty: float = 0.25  # 0 => off


def lyapunov_gate(
    previous: LyapunovState,
    current: LyapunovState,
    params: LyapunovGateParams | None = None,
    prev_slow: SlowState | None = None,
    current_slow: SlowState | None = None,
    prev_symbolic: SymbolicState | None = None,
    current_symbolic: SymbolicState | None = None,
) -> LyapunovVerdict:
    if params is None:
        params = LyapunovGateParams()
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

    # Worst-axis refusal (DM3): the mean must not average away a
    # single saturated axis.
    clamped = current.clamped()
    worst_axis = max(
        clamped.budget_used,
        clamped.risk,
        clamped.uncertainty,
        clamped.governance,
    )
    if worst_axis >= params.axis_abstain_threshold:
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
