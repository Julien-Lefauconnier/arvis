# arvis/kernel/pipeline/cognitive_pipeline.py

from __future__ import annotations

from datetime import datetime, timezone

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.pipeline.cognitive_pipeline_result import CognitivePipelineResult

from arvis.cognition.decision.decision_evaluator import DecisionEvaluator
from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder
from arvis.cognition.core.cognitive_core_engine import CognitiveCoreEngine

from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot

from arvis.cognition.control.mode_hysteresis import ModeHysteresis
from arvis.cognition.control.exploration_controller import ExplorationController
from arvis.cognition.control.regime_policy import CognitiveRegimePolicy
from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot

from arvis.math.lyapunov.lyapunov_gate import lyapunov_gate, LyapunovVerdict
from arvis.math.lyapunov.lyapunov_gate import LyapunovGateParams
from arvis.cognition.execution.executable_intent import ExecutableIntent
from arvis.math.stability.regime_estimator import CognitiveRegimeEstimator
from arvis.math.control.irg_epsilon_controller import IRGEpsilonController
from arvis.math.control.eps_adaptive import EpsAdaptiveParams, CognitiveMode
from arvis.cognition.control.temporal_pressure import TemporalPressure
from arvis.cognition.control.temporal_regulation import TemporalRegulation
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal



class CognitivePipeline:

    def __init__(self):
        self.decision = DecisionEvaluator()
        self.bundle_builder = CognitiveBundleBuilder()
        self.core = CognitiveCoreEngine(core_model=None)  # à injecter plus tard

        self.hysteresis = ModeHysteresis()
        self.exploration = ExplorationController()
        self.regime_policy = CognitiveRegimePolicy()

        self.regime_estimator = CognitiveRegimeEstimator()
        self.epsilon_controller = IRGEpsilonController(
            adaptive_params=EpsAdaptiveParams(enabled=True)
        )
        self.temporal_pressure = TemporalPressure()
        self.temporal_regulation = TemporalRegulation()

    def run(self, ctx: CognitivePipelineContext) -> CognitivePipelineResult:
        # -----------------------------------------------------
        # 1. DECISION
        # -----------------------------------------------------
        decision_result = self.decision.evaluate(ctx)
        ctx.decision_result = decision_result

        # -----------------------------------------------------
        # 2. BUNDLE
        # -----------------------------------------------------
        introspection = ctx.introspection or IntrospectionSnapshot()
        explanation = ctx.explanation or ExplanationSnapshot()

        bundle = self.bundle_builder.build(
            decision_result=decision_result,
            introspection=introspection,
            explanation=explanation,
            timeline=ctx.timeline,
        )
        ctx.bundle = bundle

        # -----------------------------------------------------
        # 3. CORE COGNITION
        # -----------------------------------------------------
        scientific = self.core.process(bundle)
        ctx.scientific_snapshot = scientific

        # Best-effort projections from scientific snapshot
        core_snapshot = getattr(scientific, "core_snapshot", None)

        ctx.collapse_risk = RiskSignal(
            getattr(scientific, "collapse_risk", 0.0) or 0.0
        )

        ctx.prev_lyap = (
            getattr(scientific, "prev_lyap", None)
            or getattr(core_snapshot, "prev_lyap", None)
        )
        ctx.cur_lyap = (
            getattr(scientific, "cur_lyap", None)
            or getattr(core_snapshot, "cur_lyap", None)
        )
        # -----------------------------------------------------
        # 3.b NORMALIZATION (Lyapunov boundary fix)
        # -----------------------------------------------------
        def _normalize_lyap(x):
            if x is None:
                return None
            if isinstance(x, LyapunovState):
                return x
            return LyapunovState.from_scalar(x)

        ctx.prev_lyap = _normalize_lyap(ctx.prev_lyap)
        ctx.cur_lyap = _normalize_lyap(ctx.cur_lyap)
        ctx.drift_score = DriftSignal(
            getattr(scientific, "drift_score", None)
            or getattr(scientific, "dv", None)
            or getattr(core_snapshot, "drift_score", None)
            or getattr(core_snapshot, "dv", 0.0)
            or 0.0
        )
        ctx.regime = (
            getattr(scientific, "regime", None)
            or getattr(core_snapshot, "regime", None)
        )
        ctx.stable = (
            getattr(scientific, "stable", None)
            if getattr(scientific, "stable", None) is not None
            else getattr(core_snapshot, "stable", None)
        )

        # -----------------------------------------------------
        # 4. REGIME ESTIMATION
        # -----------------------------------------------------

        regime_snapshot = self.regime_estimator.push(float(ctx.drift_score))

        if regime_snapshot:
            ctx.regime = regime_snapshot.regime
            regime_confidence = regime_snapshot.confidence
        else:
            ctx.regime = "transition"
            regime_confidence = 0.0

        # -----------------------------------------------------
        # 5. TEMPORAL LAYER
        # -----------------------------------------------------

        timeline = ctx.timeline or []

        total = len(timeline)

        def _timeline_text(entry) -> str:
            if isinstance(entry, dict):
                parts = [
                    entry.get("type", ""),
                    entry.get("title", ""),
                    entry.get("description", ""),
                ]
            else:
                parts = [
                    getattr(entry, "type", ""),
                    getattr(entry, "title", ""),
                    getattr(entry, "description", ""),
                ]
            return " ".join(str(p) for p in parts if p).lower()

        has_conflicts = any("conflict" in _timeline_text(e) for e in timeline)
        has_gaps = any("gap" in _timeline_text(e) for e in timeline)
        has_uncertainty = any("uncertainty" in _timeline_text(e) for e in timeline)

        healthy = True  # kernel-only (no health service)

        temporal_pressure = self.temporal_pressure.compute(
            total=total,
            has_conflicts=has_conflicts,
            has_gaps=has_gaps,
            has_uncertainty=has_uncertainty,
            healthy=healthy,
        )

        temporal_modulation = self.temporal_regulation.compute(
            total=total,
            has_conflicts=has_conflicts,
            has_gaps=has_gaps,
            has_uncertainty=has_uncertainty,
            healthy=healthy,
        )

        # Apply temporal modulation
        adjusted_risk = float(ctx.collapse_risk) * temporal_modulation.risk_multiplier
        ctx.collapse_risk = RiskSignal(adjusted_risk)

        # -----------------------------------------------------
        # 6. CONTROL
        # -----------------------------------------------------
        gate_mode_raw = self.hysteresis.update(
            user_id=ctx.user_id,
            risk=float(ctx.collapse_risk),
        )

        # ----------------------------------------------
        # 7. Convert to CognitiveMode
        # ----------------------------------------------
        if isinstance(gate_mode_raw, CognitiveMode):
            cognitive_mode = gate_mode_raw
        else:
            cognitive_mode = CognitiveMode.NORMAL

        ctx.uncertainty = UncertaintySignal(float(ctx.collapse_risk))
        # ----------------------------------------------
        # 8. IRG epsilon computation
        # ----------------------------------------------
        epsilon = self.epsilon_controller.compute(
            uncertainty=float(ctx.uncertainty),
            budget_used=0.5,
            delta_v=float(ctx.drift_score),
            collapse_risk=float(ctx.collapse_risk),
            latent_volatility=min(1.0, abs(float(ctx.drift_score))),
            mode=cognitive_mode,
        )

        regime_control = self.regime_policy.compute(ctx.regime or "neutral")

        # ----------------------------------------------
        # 9. apply modulation
        # ----------------------------------------------
        epsilon *= getattr(regime_control, "epsilon_multiplier", 1.0)
        epsilon *= getattr(temporal_modulation, "epsilon_multiplier", 1.0)

        exploration_snapshot = self.exploration.compute(
            regime=ctx.regime,
            collapse_risk=float(ctx.collapse_risk),
            drift_score=float(ctx.drift_score),
            stable=ctx.stable,
        )

        control_snapshot = CognitiveControlSnapshot(
            gate_mode=cognitive_mode,
            epsilon=float(epsilon),
            smoothed_risk=float(ctx.collapse_risk),
            lyap_verdict=LyapunovVerdict.ALLOW,  # updated below after gate
            exploration=exploration_snapshot,
            drift={
                "score": float(ctx.drift_score),
                "confidence": regime_confidence,
            },
            regime=regime_control,
            calibration=None,
        )
        ctx.control_snapshot = control_snapshot

        # -----------------------------------------------------
        # 10. GATE (Lyapunov)
        # -----------------------------------------------------
        HIGH_RISK_THRESHOLD = 0.8

        if ctx.stable is False:
            verdict = LyapunovVerdict.ABSTAIN
        elif float(ctx.collapse_risk) >= HIGH_RISK_THRESHOLD:
            verdict = LyapunovVerdict.ABSTAIN
        elif cognitive_mode == CognitiveMode.CRITICAL:
            verdict = LyapunovVerdict.ABSTAIN
        elif cognitive_mode == CognitiveMode.SAFE and ctx.cur_lyap is None:
            verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
        elif ctx.cur_lyap is None:
            verdict = LyapunovVerdict.ALLOW
        else:
            previous = ctx.prev_lyap or ctx.cur_lyap
            params = LyapunovGateParams(eps_override=epsilon)

            verdict = lyapunov_gate(
                previous=previous,
                current=ctx.cur_lyap,
                params=params,
            )

        control_snapshot = CognitiveControlSnapshot(
            gate_mode=control_snapshot.gate_mode,
            epsilon=control_snapshot.epsilon,
            smoothed_risk=control_snapshot.smoothed_risk,
            lyap_verdict=verdict,
            exploration=control_snapshot.exploration,
            drift=control_snapshot.drift,
            regime=control_snapshot.regime,
            calibration=control_snapshot.calibration,
            temporal_pressure=temporal_pressure,
            temporal_modulation=temporal_modulation,
        )
        ctx.control_snapshot = control_snapshot
        ctx.gate_result = verdict

        # -----------------------------------------------------
        # 11. EXECUTION INTENT (declarative only)
        # -----------------------------------------------------
        executable_intent = None

        if verdict == LyapunovVerdict.ALLOW:
            executable_intent = ExecutableIntent(
                bundle_id=str(getattr(bundle, "bundle_id", "bundle")),
                user_id=ctx.user_id,
                intent_signature=str(getattr(decision_result, "reason", "opaque")),
                allow_rag=True,
                max_top_k=5,
                provider="default",
                decided_at=datetime.now(timezone.utc),
                linguistic_context=None,
            )

        ctx.executable_intent = executable_intent

        return CognitivePipelineResult(
            bundle=ctx.bundle,
            decision=ctx.decision_result,
            scientific=ctx.scientific_snapshot,
            control=ctx.control_snapshot,
            gate_result=ctx.gate_result,
            executable_intent=ctx.executable_intent,
        )