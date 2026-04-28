# arvis/math/stability/hybrid_risk_observer.py

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Optional, ClassVar

from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState


def _clamp01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def _sigmoid(x: float) -> float:
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
    w_composite: Optional[float] = None
    delta_w: Optional[float] = None

    @property
    def v_total(self) -> float:
        return self.collapse_risk


@dataclass(frozen=True)
class HybridRiskParams:
    theta_num: float = 0.6
    alpha: float = 6.0
    theta_sym: float = 0.35
    beta: float = 7.0
    k: float = 2.2
    w_entropy: float = 0.35
    w_graph: float = 0.35
    w_switch: float = 0.20
    w_drift: float = 0.10


class HybridRiskObserver:
    """
    Observateur hybride risque + composite Lyapunov.
    """

    composite: ClassVar[CompositeLyapunov] = CompositeLyapunov(
        lambda_mismatch=0.5, gamma_z=1.0
    )

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
        switch = _clamp01(
            float(gate_switch_rate) + 0.5 * float(policy_disagreement_rate)
        )
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
        current_fast: Optional[LyapunovState] = None,
        current_slow: Optional[SlowState] = None,
        current_symbolic: Optional[SymbolicState] = None,
        prev_fast: Optional[LyapunovState] = None,
        prev_slow: Optional[SlowState] = None,
        prev_symbolic: Optional[SymbolicState] = None,
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

        w_composite = None
        delta_w = None

        # Calcul composite Lyapunov seulement si toutes les infos sont présentes
        if (
            current_fast is not None
            and current_slow is not None
            and current_symbolic is not None
        ):
            w_composite = HybridRiskObserver.composite.W(
                fast=current_fast,
                slow=current_slow,
                symbolic=current_symbolic,
            )

            if (
                prev_fast is not None
                and prev_slow is not None
                and prev_symbolic is not None
            ):
                delta_w = HybridRiskObserver.composite.delta_W(
                    fast_prev=prev_fast,
                    fast_next=current_fast,
                    slow_prev=prev_slow,
                    slow_next=current_slow,
                    symbolic_prev=prev_symbolic,
                    symbolic_next=current_symbolic,
                )

        return HybridRiskSnapshot(
            v_numeric=v_numeric,
            v_symbolic=v_symbolic,
            p_numeric=_clamp01(p_num),
            p_symbolic=_clamp01(p_sym),
            collapse_risk=collapse_risk,
            delta=float(delta),
            mode_hint=mode,
            early_warning=early_warning,
            w_composite=w_composite,
            delta_w=delta_w,
        )


# backward compatibility
HybridLyapunov = HybridRiskObserver
HybridLyapunovSnapshot = HybridRiskSnapshot
HybridParams = HybridRiskParams
