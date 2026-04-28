# arvis/cognition/control/cognitive_control_engine.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol, runtime_checkable

from arvis.cognition.control.cognitive_control_runtime import CognitiveControlRuntime
from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot

from arvis.math.control.eps_adaptive import CognitiveMode, EpsAdaptiveParams
from arvis.math.control.irg_epsilon_controller import (
    IRGEpsilonController,
    IRGEpsilonParams,
)
from arvis.math.lyapunov.lyapunov_gate import (
    LyapunovGateParams,
    LyapunovVerdict,
    lyapunov_gate,
)
from arvis.math.lyapunov.lyapunov import V
from arvis.math.core.normalization import clamp01

from arvis.math.signals.coercion import to_float, to_risk, to_drift, to_uncertainty


@runtime_checkable
class HasCompute(Protocol):
    def compute(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class HasUpdate(Protocol):
    def update(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class HasPush(Protocol):
    def push(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class HasSnapshot(Protocol):
    def snapshot(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class HasEvaluate(Protocol):
    def evaluate(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class HasDecide(Protocol):
    def decide(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class HasRecommend(Protocol):
    def recommend(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class HasUpdateFromRisks(Protocol):
    def update_from_risks(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class HasPushSnapshot(Protocol):
    def push(self, *args: Any, **kwargs: Any) -> Any: ...
    def snapshot(self, *args: Any, **kwargs: Any) -> Any: ...


@dataclass
class CognitiveControlDeps:
    """
    Full dependency bundle for the control engine.

    Inject concrete kernel implementations here.
    """

    epsilon_monitor_factory: Callable[..., Any] | None = None
    stability_stats: HasPushSnapshot | None = None
    adaptive_controller_factory: Callable[..., Any] | None = None
    calibration_engine: HasEvaluate | None = None
    local_dynamics_factory: Callable[..., Any] | None = None
    regime_estimator_factory: Callable[..., Any] | None = None
    drift_detector_factory: Callable[..., Any] | None = None
    regime_policy: HasCompute | None = None
    temporal_regulation: HasCompute | None = None
    temporal_pressure: HasCompute | None = None
    exploration_controller: HasCompute | None = None
    mode_hysteresis: HasUpdate | None = None
    inertia_controller: HasUpdate | None = None
    counterfactual_factory: Callable[..., Any] | None = None
    counterfactual_bandit_factory: Callable[..., Any] | None = None


class CognitiveControlEngine:
    """
    Full ARVIS control engine.

    Responsibilities:
    - fuse risk modulation
    - derive gate mode
    - compute epsilon
    - smooth risk
    - update drift/regime/dynamics
    - run adaptive/counterfactual recommendations
    - produce final Lyapunov verdict
    """

    def __init__(self, deps: CognitiveControlDeps):
        self.deps = deps
        self._irg_epsilon = IRGEpsilonController(
            adaptive_params=EpsAdaptiveParams(enabled=True),
            irg_params=IRGEpsilonParams(enabled=True),
        )

    @staticmethod
    def _budget_ratio(budget: Any) -> float:
        try:
            return float(budget.current_changes / max(1, budget.max_changes))
        except Exception:
            return 0.0

    def compute(
        self,
        *,
        runtime: CognitiveControlRuntime,
        user_id: str,
        bundle: Any,
        budget: Any,
        core: Any,
        prev_lyap: Any,
        cur_lyap: Any,
        irg: Any,
        explanation: Any | None = None,
    ) -> CognitiveControlSnapshot:
        fused_risk = clamp01(to_float(getattr(core, "fused_risk", 0.0), 0.0))

        # ----------------------------------
        # Temporal pressure
        # ----------------------------------
        temporal_pressure = None
        try:
            if self.deps.temporal_pressure is not None:
                temporal_pressure = self.deps.temporal_pressure.compute(user_id)
                fused_risk = clamp01(
                    fused_risk
                    + 0.2 * to_float(getattr(temporal_pressure, "pressure", 0.0), 0.0)
                )
        except Exception:
            temporal_pressure = None

        # ----------------------------------
        # Temporal modulation
        # ----------------------------------
        temporal_modulation = None
        try:
            if self.deps.temporal_regulation is not None:
                temporal_modulation = self.deps.temporal_regulation.compute(user_id)
                fused_risk = clamp01(
                    fused_risk
                    * to_float(
                        getattr(temporal_modulation, "risk_multiplier", 1.0), 1.0
                    )
                )
        except Exception:
            temporal_modulation = None

        # ----------------------------------
        # Gate mode
        # ----------------------------------
        gate_mode = CognitiveMode.NORMAL
        try:
            mh_snapshot = getattr(core, "mh_snapshot", None)
            if (
                mh_snapshot is not None
                and getattr(mh_snapshot, "mode_hint", None) == "safe"
            ):
                gate_mode = CognitiveMode.SAFE
        except Exception:
            gate_mode = CognitiveMode.NORMAL

        try:
            if self.deps.mode_hysteresis is not None:
                gate_mode = self.deps.mode_hysteresis.update(user_id, fused_risk)
        except Exception:
            pass

        # ----------------------------------
        # Latent volatility
        # ----------------------------------
        latent_volatility = 0.0
        try:
            wp = getattr(core, "world_prediction", None)
            latent = getattr(wp, "latent", None) if wp is not None else None
            if latent is not None and len(latent) > 0:
                latent_volatility = to_float(latent[0], 0.0)
        except Exception:
            latent_volatility = 0.0

        # ----------------------------------
        # Epsilon
        # ----------------------------------
        uncertainty = 0.5
        try:
            wp = getattr(core, "world_prediction", None)
            uncertainty = to_float(getattr(wp, "uncertainty", 0.5), 0.5)
        except Exception:
            pass

        budget_ratio = self._budget_ratio(budget)

        risk_signal = to_risk(fused_risk)
        uncertainty_signal = to_uncertainty(uncertainty)
        drift_signal = to_drift(getattr(core, "dv", 0.0))
        latent_volatility_signal = to_drift(latent_volatility)

        eps = self._irg_epsilon.compute(
            uncertainty=uncertainty_signal,
            budget_used=budget_ratio,
            delta_v=drift_signal,
            collapse_risk=risk_signal,
            latent_volatility=latent_volatility_signal,
            mode=gate_mode,
        )

        try:
            if temporal_modulation is not None:
                eps = float(eps) * to_float(
                    getattr(temporal_modulation, "epsilon_multiplier", 1.0), 1.0
                )
        except Exception:
            pass

        # ----------------------------------
        # Base Lyapunov verdict
        # ----------------------------------
        gate_params = LyapunovGateParams(mode=gate_mode, eps_override=eps)

        if prev_lyap is None:
            lyap_verdict = lyapunov_gate(cur_lyap, cur_lyap, gate_params)
        else:
            lyap_verdict = lyapunov_gate(prev_lyap, cur_lyap, gate_params)

        if gate_mode == CognitiveMode.CRITICAL:
            lyap_verdict = LyapunovVerdict.ABSTAIN

        # ----------------------------------
        # Inertia smoothing
        # ----------------------------------
        smoothed_risk = fused_risk
        try:
            if self.deps.inertia_controller is not None:
                inertia_snapshot = self.deps.inertia_controller.update(
                    user_id=user_id,
                    collapse_risk=fused_risk,
                )
                smoothed_risk = to_float(
                    getattr(inertia_snapshot, "smoothed_risk", fused_risk), fused_risk
                )
                runtime.inertia_risk = smoothed_risk
        except Exception:
            smoothed_risk = fused_risk

        # ----------------------------------
        # Drift / regime / exploration
        # ----------------------------------
        drift_snapshot = None
        regime_snapshot = None
        exploration_snapshot = None
        calibration_snapshot = None

        try:
            if runtime.epsilon_monitor is None and self.deps.epsilon_monitor_factory:
                runtime.epsilon_monitor = self.deps.epsilon_monitor_factory()

            if runtime.epsilon_monitor is not None and isinstance(
                runtime.epsilon_monitor, HasPush
            ):
                runtime.epsilon_monitor.push(to_float(getattr(core, "dv", 0.0), 0.0))
        except Exception:
            pass

        try:
            if self.deps.stability_stats is not None and isinstance(
                self.deps.stability_stats, HasPushSnapshot
            ):
                self.deps.stability_stats.push(
                    user_id, to_float(getattr(core, "dv", 0.0), 0.0)
                )
                stats = self.deps.stability_stats.snapshot(user_id)

                if stats and getattr(stats, "samples", 0) > 20:
                    if (
                        runtime.drift_detector is None
                        and self.deps.drift_detector_factory
                    ):
                        runtime.drift_detector = self.deps.drift_detector_factory()

                    if runtime.drift_detector is not None and isinstance(
                        runtime.drift_detector, HasEvaluate
                    ):
                        drift_snapshot = runtime.drift_detector.evaluate(
                            contraction_rate=to_float(stats.contraction_rate, 0.0),
                            instability_rate=to_float(stats.instability_rate, 0.0),
                        )
        except Exception:
            pass

        try:
            if runtime.regime_estimator is None and self.deps.regime_estimator_factory:
                runtime.regime_estimator = self.deps.regime_estimator_factory()

            if runtime.regime_estimator is not None and isinstance(
                runtime.regime_estimator, HasPush
            ):
                regime_snapshot = runtime.regime_estimator.push(
                    to_float(getattr(core, "dv", 0.0), 0.0)
                )

            if regime_snapshot is not None and self.deps.regime_policy is not None:
                runtime.regime_control = self.deps.regime_policy.compute(
                    regime_snapshot.regime
                )
        except Exception:
            pass

        try:
            if self.deps.exploration_controller is not None:
                regime_name = (
                    getattr(runtime.regime_control, "mode", None)
                    if runtime.regime_control
                    else None
                )
                drift_score = to_float(
                    getattr(drift_snapshot, "drift_score", 0.0)
                    if drift_snapshot
                    else 0.0,
                    0.0,
                )

                exploration_snapshot = self.deps.exploration_controller.compute(
                    regime=regime_name,
                    collapse_risk=to_risk(smoothed_risk),
                    drift_score=to_drift(drift_score),
                    stable=None,
                )
                runtime.exploration_state = exploration_snapshot

                irg_factor = 1.0
                try:
                    irg_state = irg.snapshot()
                    structural = to_float(
                        getattr(irg_state, "structural_risk", 0.0), 0.0
                    )
                    irg_factor = max(0.05, min(1.0, 1.0 - structural))
                except Exception:
                    irg_factor = 1.0

                try:
                    scaled = int(
                        max(
                            1,
                            to_float(budget.max_changes, 1.0)
                            * to_float(
                                getattr(
                                    exploration_snapshot, "change_budget_scale", 1.0
                                ),
                                1.0,
                            )
                            * to_float(irg_factor, 1.0),
                        )
                    )
                    budget.max_changes = scaled
                except Exception:
                    pass
        except Exception:
            pass

        # ----------------------------------
        # Local dynamics
        # ----------------------------------
        try:
            if runtime.local_dynamics is None and self.deps.local_dynamics_factory:
                runtime.local_dynamics = self.deps.local_dynamics_factory()

            if runtime.local_dynamics is not None and isinstance(
                runtime.local_dynamics, HasPush
            ):
                runtime.local_dynamics.push(
                    delta_v=to_float(getattr(core, "dv", 0.0), 0.0),
                    features={
                        "budget_ratio": self._budget_ratio(budget),
                        "collapse_risk": to_float(smoothed_risk, 0.0),
                        "V": float(V(cur_lyap)),
                    },
                )
        except Exception:
            pass

        # ----------------------------------
        # Adaptive controller
        # ----------------------------------
        try:
            adaptive = None
            if self.deps.adaptive_controller_factory is not None:
                adaptive = self.deps.adaptive_controller_factory(user_id)

            if adaptive is not None:
                adaptive_snapshot = adaptive.compute(
                    collapse_risk=to_float(smoothed_risk, 0.0),
                    drift_score=getattr(drift_snapshot, "drift_score", None)
                    if drift_snapshot
                    else None,
                )

                mode = str(getattr(adaptive_snapshot, "mode", "")).lower()
                if mode == "safe":
                    lyap_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
                elif mode in {"abstain", "critical"}:
                    lyap_verdict = LyapunovVerdict.ABSTAIN
        except Exception:
            pass

        # ----------------------------------
        # Counterfactual simulator
        # ----------------------------------
        cf_force_abstain = False
        cf_force_confirm = False

        try:
            if runtime.counterfactual is None and self.deps.counterfactual_factory:
                runtime.counterfactual = self.deps.counterfactual_factory()

            if runtime.counterfactual is not None and isinstance(
                runtime.counterfactual, HasDecide
            ):
                cf_decision = runtime.counterfactual.decide(
                    base_risk=to_float(smoothed_risk, 0.0),
                    base_uncertainty=to_float(uncertainty, 0.5),
                )

                if getattr(cf_decision, "best_action", None) == "abstain":
                    cf_force_abstain = True
                elif getattr(cf_decision, "best_action", None) == "confirm":
                    cf_force_confirm = True
        except Exception:
            pass

        if cf_force_abstain:
            lyap_verdict = LyapunovVerdict.ABSTAIN
        elif cf_force_confirm and lyap_verdict != LyapunovVerdict.ABSTAIN:
            lyap_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        # ----------------------------------
        # Adaptive bandit
        # ----------------------------------
        try:
            if runtime.cf_bandit is None and self.deps.counterfactual_bandit_factory:
                runtime.cf_bandit = self.deps.counterfactual_bandit_factory(user_id)

            if runtime.cf_bandit is not None and isinstance(
                runtime.cf_bandit, HasRecommend
            ):
                if (
                    runtime.last_action is not None
                    and runtime.last_risk is not None
                    and isinstance(runtime.cf_bandit, HasUpdateFromRisks)
                ):
                    runtime.cf_bandit.update_from_risks(
                        action=str(runtime.last_action),
                        prev_risk=to_float(runtime.last_risk, 0.0),
                        current_risk=to_float(smoothed_risk, 0.0),
                    )

                rec = runtime.cf_bandit.recommend(
                    current_risk=to_float(smoothed_risk, 0.0)
                )

                if (
                    rec == "abstain"
                    and to_float(smoothed_risk, 0.0) >= 0.70
                    and not cf_force_abstain
                ):
                    lyap_verdict = LyapunovVerdict.ABSTAIN
                elif (
                    rec == "confirm"
                    and to_float(smoothed_risk, 0.0) >= 0.35
                    and not cf_force_abstain
                ):
                    lyap_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
        except Exception:
            pass

        runtime.last_risk = to_float(smoothed_risk, 0.0)
        if lyap_verdict == LyapunovVerdict.ABSTAIN:
            runtime.last_action = "abstain"
        elif lyap_verdict == LyapunovVerdict.REQUIRE_CONFIRMATION:
            runtime.last_action = "confirm"
        else:
            runtime.last_action = "allow"

        # ----------------------------------
        # Passive calibration
        # ----------------------------------
        try:
            if self.deps.calibration_engine is not None and drift_snapshot is not None:
                calibration_snapshot = self.deps.calibration_engine.evaluate([])
        except Exception:
            calibration_snapshot = None

        smoothed_risk = clamp01(float(smoothed_risk))

        return CognitiveControlSnapshot(
            gate_mode=gate_mode,
            epsilon=float(eps),
            smoothed_risk=float(smoothed_risk),
            lyap_verdict=lyap_verdict,
            exploration=exploration_snapshot,
            drift=drift_snapshot,
            regime=regime_snapshot,
            calibration=calibration_snapshot,
            temporal_pressure=temporal_pressure,
            temporal_modulation=temporal_modulation,
        )
