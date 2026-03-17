# arvis/cognition/control/cognitive_control_engine.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from arvis.cognition.control.cognitive_control_runtime import CognitiveControlRuntime
from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot

from arvis.math.control.eps_adaptive import CognitiveMode, EpsAdaptiveParams
from arvis.math.control.irg_epsilon_controller import IRGEpsilonController, IRGEpsilonParams
from arvis.math.lyapunov.lyapunov_gate import (
    LyapunovGateParams,
    LyapunovVerdict,
    lyapunov_gate,
)
from arvis.math.lyapunov.lyapunov import V
from arvis.math.core.normalization import clamp01
from arvis.math.core.control_inertia import RegimeInertiaController

from arvis.math.drift.drift_detector import DriftDetector
from arvis.math.stability.regime_estimator import CognitiveRegimeEstimator
from arvis.cognition.control.temporal_modulation import TemporalModulation
from arvis.cognition.control.exploration_snapshot import ExplorationSnapshot
from arvis.cognition.control.regime_control_snapshot import RegimeControlSnapshot
from arvis.cognition.control.adaptive_mode_snapshot import AdaptiveModeSnapshot


@dataclass
class CognitiveControlDeps:
    """
    Full dependency bundle for the control engine.

    Inject concrete kernel implementations here.
    """

    epsilon_monitor_factory: callable | None = None
    stability_stats: object | None = None
    adaptive_controller_factory: callable | None = None
    calibration_engine: object | None = None
    local_dynamics_factory: callable | None = None
    regime_estimator_factory: callable | None = None
    regime_policy: object | None = None
    temporal_regulation: object | None = None
    temporal_pressure: object | None = None
    exploration_controller: object | None = None
    mode_hysteresis: object | None = None
    inertia_controller: object | None = None
    counterfactual_factory: callable | None = None
    counterfactual_bandit_factory: callable | None = None


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

    def compute(
        self,
        *,
        runtime: CognitiveControlRuntime,
        user_id: str,
        bundle,
        budget,
        core,
        prev_lyap,
        cur_lyap,
        irg,
        explanation=None,
    ) -> CognitiveControlSnapshot:
        fused_risk = clamp01(float(getattr(core, "fused_risk", 0.0) or 0.0))

        # ----------------------------------
        # Temporal pressure
        # ----------------------------------
        temporal_pressure = None
        try:
            if self.deps.temporal_pressure is not None:
                temporal_pressure = self.deps.temporal_pressure.compute(user_id)
                fused_risk = clamp01(
                    float(fused_risk) + 0.2 * float(getattr(temporal_pressure, "pressure", 0.0))
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
                    float(fused_risk) * float(getattr(temporal_modulation, "risk_multiplier", 1.0))
                )
        except Exception:
            temporal_modulation = None

        # ----------------------------------
        # Gate mode
        # ----------------------------------
        gate_mode = CognitiveMode.NORMAL
        try:
            mh_snapshot = getattr(core, "mh_snapshot", None)
            if mh_snapshot is not None and getattr(mh_snapshot, "mode_hint", None) == "safe":
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
                latent_volatility = float(latent[0])
        except Exception:
            latent_volatility = 0.0

        # ----------------------------------
        # Epsilon
        # ----------------------------------
        uncertainty = 0.5
        try:
            wp = getattr(core, "world_prediction", None)
            uncertainty = float(getattr(wp, "uncertainty", 0.5) or 0.5)
        except Exception:
            pass

        budget_ratio = 0.0
        try:
            budget_ratio = float(budget.current_changes / max(1, budget.max_changes))
        except Exception:
            budget_ratio = 0.0

        eps = self._irg_epsilon.compute(
            uncertainty=uncertainty,
            budget_used=budget_ratio,
            delta_v=float(getattr(core, "dv", 0.0) or 0.0),
            collapse_risk=fused_risk,
            latent_volatility=latent_volatility,
            mode=gate_mode,
        )

        try:
            if temporal_modulation is not None:
                eps = float(eps) * float(getattr(temporal_modulation, "epsilon_multiplier", 1.0))
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
                smoothed_risk = float(getattr(inertia_snapshot, "smoothed_risk", fused_risk))
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

            if runtime.epsilon_monitor is not None:
                runtime.epsilon_monitor.push(float(getattr(core, "dv", 0.0) or 0.0))
        except Exception:
            pass

        try:
            if self.deps.stability_stats is not None:
                self.deps.stability_stats.push(user_id, float(getattr(core, "dv", 0.0) or 0.0))
                stats = self.deps.stability_stats.snapshot(user_id)

                if stats and getattr(stats, "samples", 0) > 20:
                    if runtime.drift_detector is None and self.deps.drift_detector_factory:
                        runtime.drift_detector = self.deps.drift_detector_factory()

                    if runtime.drift_detector is not None:
                        drift_snapshot = runtime.drift_detector.evaluate(
                            contraction_rate=stats.contraction_rate,
                            instability_rate=stats.instability_rate,
                        )
        except Exception:
            pass

        try:
            if runtime.regime_estimator is None and self.deps.regime_estimator_factory:
                runtime.regime_estimator = self.deps.regime_estimator_factory()

            if runtime.regime_estimator is not None:
                regime_snapshot = runtime.regime_estimator.push(float(getattr(core, "dv", 0.0) or 0.0))

            if regime_snapshot is not None and self.deps.regime_policy is not None:
                runtime.regime_control = self.deps.regime_policy.compute(regime_snapshot.regime)
        except Exception:
            pass

        try:
            if self.deps.exploration_controller is not None:
                regime_name = getattr(runtime.regime_control, "mode", None) if runtime.regime_control else None
                drift_score = getattr(drift_snapshot, "drift_score", 0.0) if drift_snapshot else 0.0

                exploration_snapshot = self.deps.exploration_controller.compute(
                    regime=regime_name,
                    collapse_risk=smoothed_risk,
                    drift_score=drift_score,
                    stable=None,
                )
                runtime.exploration_state = exploration_snapshot

                irg_factor = 1.0
                try:
                    irg_state = irg.snapshot()
                    structural = float(getattr(irg_state, "structural_risk", 0.0) or 0.0)
                    irg_factor = max(0.05, min(1.0, 1.0 - structural))
                except Exception:
                    irg_factor = 1.0

                try:
                    scaled = int(
                        max(
                            1,
                            float(budget.max_changes)
                            * float(getattr(exploration_snapshot, "change_budget_scale", 1.0))
                            * float(irg_factor),
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

            if runtime.local_dynamics is not None:
                runtime.local_dynamics.push(
                    delta_v=float(getattr(core, "dv", 0.0) or 0.0),
                    features={
                        "budget_ratio": float(budget.current_changes) / float(max(1, budget.max_changes)),
                        "collapse_risk": float(smoothed_risk),
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
                    collapse_risk=float(smoothed_risk),
                    drift_score=getattr(drift_snapshot, "drift_score", None) if drift_snapshot else None,
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

            if runtime.counterfactual is not None:
                cf_decision = runtime.counterfactual.decide(
                    base_risk=float(smoothed_risk),
                    base_uncertainty=float(uncertainty),
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

            if runtime.cf_bandit is not None:
                if runtime.last_action is not None and runtime.last_risk is not None:
                    runtime.cf_bandit.update_from_risks(
                        action=str(runtime.last_action),
                        prev_risk=float(runtime.last_risk),
                        current_risk=float(smoothed_risk),
                    )

                rec = runtime.cf_bandit.recommend(current_risk=float(smoothed_risk))

                if rec == "abstain" and float(smoothed_risk) >= 0.70 and not cf_force_abstain:
                    lyap_verdict = LyapunovVerdict.ABSTAIN
                elif rec == "confirm" and float(smoothed_risk) >= 0.35 and not cf_force_abstain:
                    lyap_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
        except Exception:
            pass

        runtime.last_risk = float(smoothed_risk)
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