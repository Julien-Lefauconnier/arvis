# arvis/math/stability/hybrid_risk_observer.py

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional


def _clamp01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def _sigmoid(x: float) -> float:
    # numerically stable sigmoid
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


@dataclass(frozen=True)
class HybridRiskSnapshot:
    """
    Snapshot produced by the hybrid risk observer.

    collapse_risk ∈ [0,1] represents estimated probability
    of cognitive instability / collapse.
    """
    v_numeric: float
    v_symbolic: float

    p_numeric: float
    p_symbolic: float

    collapse_risk: float
    delta: float

    mode_hint: str
    early_warning: bool

    # backward compatibility
    @property
    def v_total(self) -> float:
        return self.collapse_risk

@dataclass(frozen=True)
class HybridRiskParams:

    # numeric gate
    theta_num: float = 0.6
    alpha: float = 6.0

    # symbolic gate
    theta_sym: float = 0.35
    beta: float = 7.0

    # symbolic energy weights
    k: float = 2.2
    w_entropy: float = 0.35
    w_graph: float = 0.35
    w_switch: float = 0.20
    w_drift: float = 0.10


class HybridRiskObserver:

    @staticmethod
    def symbolic_energy(
        *,
        conflict_entropy: float,
        contradiction_density: float,
        gate_switch_rate: float,
        policy_disagreement_rate: float,
        symbolic_drift_score: float,
        edges_count: int,
        mean_edge_weight: float,
        max_edge_weight: float,
        spectral_proxy: float,
        params: Optional[HybridRiskParams] = None,
    ) -> float:

        if params is None:
            params = HybridRiskParams()

        graph_raw = math.log1p(max(0, edges_count)) * float(max(0.0, mean_edge_weight))
        graph = _clamp01(graph_raw / 3.0)

        contr = 1.0 - math.exp(-float(max(0.0, contradiction_density)) / 3.0)
        contr = _clamp01(contr)

        switch = _clamp01(float(gate_switch_rate) + 0.5 * float(policy_disagreement_rate))

        ent = _clamp01(float(conflict_entropy))
        drift = _clamp01(float(symbolic_drift_score))

        x = (
            params.w_entropy * ent
            + params.w_graph * _clamp01(graph + 0.5 * contr)
            + params.w_switch * switch
            + params.w_drift * drift
        )

        v_sym = 1.0 - math.exp(-params.k * _clamp01(x))

        return _clamp01(v_sym)

    @staticmethod
    def fuse(
        *,
        v_numeric: float,
        v_symbolic: float,
        prev_v_total: Optional[float] = None,
        prev_collapse_risk: Optional[float] = None,
        params: HybridRiskParams = HybridRiskParams(),
    ) -> HybridRiskSnapshot:

        v_numeric = _clamp01(float(v_numeric))
        v_symbolic = _clamp01(float(v_symbolic))

        p_num = _sigmoid(params.alpha * (v_numeric - params.theta_num))
        p_sym = _sigmoid(params.beta * (v_symbolic - params.theta_sym))

        collapse_risk = 1.0 - (1.0 - p_num) * (1.0 - p_sym)
        collapse_risk = _clamp01(collapse_risk)

        prev = prev_collapse_risk if prev_collapse_risk is not None else prev_v_total
        delta = 0.0 if prev is None else float(collapse_risk - prev)

        early_warning = bool(collapse_risk >= 0.55 or delta > 0.08)

        if collapse_risk >= 0.75:
            mode = "critical"
        elif collapse_risk >= 0.55:
            mode = "safe"
        else:
            mode = "normal"

        return HybridRiskSnapshot(
            v_numeric=v_numeric,
            v_symbolic=v_symbolic,
            p_numeric=_clamp01(p_num),
            p_symbolic=_clamp01(p_sym),
            collapse_risk=collapse_risk,
            delta=float(delta),
            mode_hint=mode,
            early_warning=early_warning,
        )


# -----------------------------------------------------------
# backward compatibility
# -----------------------------------------------------------

HybridLyapunov = HybridRiskObserver
HybridLyapunovSnapshot = HybridRiskSnapshot
HybridParams = HybridRiskParams