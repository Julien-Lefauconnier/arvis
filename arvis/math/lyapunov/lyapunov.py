# arvis/math/lyuapunov/lyapunov.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.core.normalization import clamp01


@dataclass(frozen=True)
class LyapunovWeights:
    """
    Convex weights for the Lyapunov candidate V in [0,1].

    Ensures sum(w)=1 (or defaults to uniform if degenerate).
    """
    w_budget: float = 0.25
    w_risk: float = 0.25
    w_uncertainty: float = 0.25
    w_governance: float = 0.25

    def normalized(self) -> "LyapunovWeights":
        wb = max(0.0, float(self.w_budget))
        wr = max(0.0, float(self.w_risk))
        wu = max(0.0, float(self.w_uncertainty))
        wg = max(0.0, float(self.w_governance))

        s = wb + wr + wu + wg
        if s <= 1e-12:
            return LyapunovWeights(0.25, 0.25, 0.25, 0.25)

        return LyapunovWeights(
            wb / s,
            wr / s,
            wu / s,
            wg / s,
        )


@dataclass(frozen=True)
class LyapunovState:
    """
    Signals composing the Lyapunov candidate.

    All signals must be normalized in [0,1].
    """
    budget_used: float
    risk: float
    uncertainty: float
    governance: float

    def clamped(self) -> "LyapunovState":
        return LyapunovState(
            budget_used=clamp01(self.budget_used),
            risk=clamp01(self.risk),
            uncertainty=clamp01(self.uncertainty),
            governance=clamp01(self.governance),
        )


def lyapunov_value(
    state: LyapunovState,
    weights: LyapunovWeights | None = None,
) -> float:
    """
    Constructive Lyapunov candidate.

    V(x) ∈ [0,1] defined as convex combination of normalized signals.
    """
    w = (weights or LyapunovWeights()).normalized()
    s = state.clamped()

    value = (
        w.w_budget * s.budget_used
        + w.w_risk * s.risk
        + w.w_uncertainty * s.uncertainty
        + w.w_governance * s.governance
    )

    return clamp01(value)


def lyapunov_delta(
    prev: LyapunovState,
    nxt: LyapunovState,
    weights: LyapunovWeights | None = None,
) -> float:
    """
    ΔV = V(next) - V(prev)
    """
    return lyapunov_value(nxt, weights=weights) - lyapunov_value(prev, weights=weights)


def sufficient_eps_bound(
    prev: LyapunovState,
    nxt: LyapunovState,
    eps: float,
    weights: LyapunovWeights | None = None,
) -> bool:
    """
    Utility for tests / invariants:
    checks ΔV <= eps (with eps clamped >=0).
    """
    eps = max(0.0, float(eps))
    return lyapunov_delta(prev, nxt, weights=weights) <= eps + 1e-12


# ------------------------------------------------------------------
# Backward compatibility layer (temporary)
# ------------------------------------------------------------------

# legacy names used in the current codebase
V = lyapunov_value
delta_V = lyapunov_delta