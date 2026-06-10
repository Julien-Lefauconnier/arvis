# arvis/math/core/contraction_monitor_core.py
"""v0 certified governed contraction monitor.

Maps a cognitive ``bundle`` and the previous replayable ``ScientificState`` to a
measured scientific snapshot: a four-axis Lyapunov state, its scalar energy ``V``
and ``delta_v`` (contraction signal), a PAC upper-confidence risk bound, a hybrid
drift, and an empirical regime. Pure transition:
``compute(bundle, prior) -> (snapshot, next)``.

This is intentionally a *monitor* (measured energy + certified risk + replay), not a
proven Lyapunov function: the composite-W (slow/symbolic coupling, small-gain) stays
out of scope until the fast loop is validated empirically. No side effects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from arvis.math.core.normalization import clamp01
from arvis.math.drift.drift import hybrid_drift
from arvis.math.lyapunov.lyapunov import LyapunovState, lyapunov_value
from arvis.math.risk.risk_bound import (
    HoeffdingRiskBound,
    RiskBoundParams,
    RiskBoundSnapshot,
)
from arvis.math.stability.regime_estimator import (
    CognitiveRegimeEstimator,
    RegimeSnapshot,
)


def _default_intent_governance() -> Mapping[str, float]:
    return {
        "action_request": 1.0,
        "search": 0.5,
        "informational_query": 0.2,
        "unknown": 0.6,
    }


@dataclass(frozen=True)
class MonitorConfig:
    """Calibratable v0 constants. Defaults match the v0 contract."""

    tau_risk: float = 0.5
    uncertainty_saturation: int = 4
    drift_alpha: float = 0.5
    governance_default: float = 0.6
    risk_window: int = 200
    risk_delta: float = 0.01
    regime_window: int = 40
    regime_min_samples: int = 10
    intent_governance: Mapping[str, float] = field(
        default_factory=_default_intent_governance
    )


@dataclass(frozen=True)
class ScientificState:
    """Compact, serializable, replayable cross-turn state (option b-i).

    Crosses the veramem<->arvis boundary as a plain JSON dict (see to_dict/from_dict);
    veramem treats it as an opaque blob and never imports this type.
    """

    prev_lyap: tuple[float, float, float, float] | None
    prev_roles: tuple[str, ...]
    risk_window: tuple[int, ...]
    regime_window: tuple[float, ...]
    turn_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "prev_lyap": list(self.prev_lyap) if self.prev_lyap is not None else None,
            "prev_roles": list(self.prev_roles),
            "risk_window": list(self.risk_window),
            "regime_window": list(self.regime_window),
            "turn_index": self.turn_index,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any] | None) -> ScientificState | None:
        if not raw:
            return None
        pl = raw.get("prev_lyap")
        prev_lyap: tuple[float, float, float, float] | None = None
        if pl is not None:
            prev_lyap = (
                float(pl[0]),
                float(pl[1]),
                float(pl[2]),
                float(pl[3]),
            )
        return cls(
            prev_lyap=prev_lyap,
            prev_roles=tuple(str(r) for r in raw.get("prev_roles", ())),
            risk_window=tuple(int(x) for x in raw.get("risk_window", ())),
            regime_window=tuple(float(x) for x in raw.get("regime_window", ())),
            turn_index=int(raw.get("turn_index", 0)),
        )


@dataclass(frozen=True)
class MonitorSnapshot:
    """core_snapshot shape consumed by CognitiveCoreEngine.process / CoreStage.

    Field names match the engine's or-fallbacks (collapse_risk, drift_score).
    """

    collapse_risk: float
    drift_score: float
    cur_lyap: LyapunovState
    prev_lyap: LyapunovState | None
    energy_v: float
    delta_v: float
    regime: str
    stable: bool
    risk_ucb: float
    risk_verdict: str


class ContractionMonitorCore:
    """v0 contraction monitor.

    Pure transition; no slow/symbolic state, no composite-W.
    """

    def __init__(self, config: MonitorConfig | None = None) -> None:
        self._cfg = config or MonitorConfig()

    def compute(
        self, bundle: Any, prior: ScientificState | None
    ) -> tuple[MonitorSnapshot, ScientificState]:
        cfg = self._cfg
        retr = getattr(bundle, "retrieval_snapshot", None)
        decision = getattr(bundle, "decision_result", None)
        memory_features = getattr(bundle, "memory_features", None) or {}

        # --- four measured signals, each in [0, 1] ---
        risk = self._risk_signal(retr)
        uncertainty = self._uncertainty_signal(decision)
        governance = self._governance_signal(decision)
        budget_used = clamp01(float(memory_features.get("memory_pressure", 0.0) or 0.0))

        cur_lyap = LyapunovState(
            budget_used=budget_used,
            risk=risk,
            uncertainty=uncertainty,
            governance=governance,
        ).clamped()
        cur_vec: tuple[float, float, float, float] = (
            cur_lyap.budget_used,
            cur_lyap.risk,
            cur_lyap.uncertainty,
            cur_lyap.governance,
        )
        energy_v = float(lyapunov_value(cur_lyap))

        # --- previous fast state (delta_v = 0 on the first turn) ---
        prev_lyap_state: LyapunovState | None = None
        prev_v = energy_v
        if prior is not None and prior.prev_lyap is not None:
            prev_lyap_state = LyapunovState(
                budget_used=prior.prev_lyap[0],
                risk=prior.prev_lyap[1],
                uncertainty=prior.prev_lyap[2],
                governance=prior.prev_lyap[3],
            ).clamped()
            prev_v = float(lyapunov_value(prev_lyap_state))
        delta_v = energy_v - prev_v

        # --- hybrid drift between previous and current state ---
        cur_roles = (
            tuple(str(r) for r in (getattr(retr, "semantic_roles", None) or ()))
            if retr is not None
            else ()
        )
        if prior is not None and prior.prev_lyap is not None:
            drift_score = float(
                hybrid_drift(
                    continuous_a=prior.prev_lyap,
                    continuous_b=cur_vec,
                    symbolic_a=set(prior.prev_roles),
                    symbolic_b=set(cur_roles),
                    alpha=cfg.drift_alpha,
                )
            )
        else:
            drift_score = 0.0

        # --- risk: empirical windowed rate (collapse_risk) + PAC ceiling (risk_ucb) ---
        violation = (risk >= cfg.tau_risk) or (uncertainty > 0.0)
        prior_risk_window = prior.risk_window if prior is not None else ()
        risk_window = (prior_risk_window + (1 if violation else 0,))[-cfg.risk_window :]
        collapse_risk, risk_ucb, risk_verdict = self._pac_risk(risk_window)

        # --- empirical regime over the delta_v history ---
        prior_regime_window = prior.regime_window if prior is not None else ()
        regime_window = (prior_regime_window + (delta_v,))[-cfg.regime_window :]
        regime = self._regime(regime_window)
        stable = delta_v <= 0.0

        snapshot = MonitorSnapshot(
            collapse_risk=collapse_risk,
            drift_score=drift_score,
            cur_lyap=cur_lyap,
            prev_lyap=prev_lyap_state,
            energy_v=energy_v,
            delta_v=delta_v,
            regime=regime,
            stable=stable,
            risk_ucb=risk_ucb,
            risk_verdict=risk_verdict,
        )
        nxt = ScientificState(
            prev_lyap=cur_vec,
            prev_roles=cur_roles,
            risk_window=risk_window,
            regime_window=regime_window,
            turn_index=(prior.turn_index + 1) if prior is not None else 0,
        )
        return snapshot, nxt

    # ------------------------------------------------------------------
    # Signal extraction (v0 formulas; all outputs clamped to [0, 1])
    # ------------------------------------------------------------------
    @staticmethod
    def _risk_signal(retr: Any) -> float:
        if retr is None:
            return 0.0
        conf = getattr(retr, "confidence", None)
        if conf is None:
            scores = getattr(retr, "scores", None) or ()
            conf = max(scores) if scores else 0.0
        return clamp01(1.0 - float(conf))

    def _uncertainty_signal(self, decision: Any) -> float:
        frames = getattr(decision, "uncertainty_frames", None) or ()
        total_axes = sum(len(getattr(f, "axes", None) or ()) for f in frames)
        k = max(1, self._cfg.uncertainty_saturation)
        return clamp01(total_axes / k)

    def _governance_signal(self, decision: Any) -> float:
        reason = getattr(decision, "reason", None) or "unknown"
        level = self._cfg.intent_governance.get(reason, self._cfg.governance_default)
        return clamp01(float(level))

    def _pac_risk(self, window: tuple[int, ...]) -> tuple[float, float, str]:
        """Return (empirical_rate p_hat, certified_ceiling p_ucb, verdict).

        p_hat is the observed violation rate over the window (moves immediately,
        discriminates nominal vs risky). p_ucb is the Hoeffding upper-confidence
        ceiling: honest about sampling, stays cautious until enough evidence.
        """
        bound = HoeffdingRiskBound(
            RiskBoundParams(
                window_size=self._cfg.risk_window, delta=self._cfg.risk_delta
            )
        )
        snap: RiskBoundSnapshot | None = None
        for event in window:
            snap = bound.push(bool(event))
        if snap is None:
            return 0.0, 0.0, "OK"
        return float(snap.p_hat), float(snap.p_ucb), str(snap.verdict)

    def _regime(self, window: tuple[float, ...]) -> str:
        estimator = CognitiveRegimeEstimator(
            window=self._cfg.regime_window,
            min_samples=self._cfg.regime_min_samples,
        )
        snap: RegimeSnapshot | None = None
        for delta_v in window:
            snap = estimator.push(delta_v)
        return "warmup" if snap is None else str(snap.regime)
