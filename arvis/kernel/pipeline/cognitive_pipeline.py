# arvis/kernel/pipeline/cognitive_pipeline.py

from __future__ import annotations

from datetime import datetime, timezone
import os
import warnings
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from typing import Any, cast, Protocol, Dict

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.pipeline.cognitive_pipeline_result import CognitivePipelineResult

from arvis.cognition.decision.decision_evaluator import DecisionEvaluator
from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder
from arvis.cognition.core.cognitive_core_engine import CognitiveCoreEngine


from arvis.cognition.control.mode_hysteresis import ModeHysteresis
from arvis.cognition.control.exploration_controller import ExplorationController
from arvis.cognition.control.regime_policy import CognitiveRegimePolicy
from arvis.cognition.control.cognitive_control_runtime import CognitiveControlRuntime

from arvis.math.stability.regime_estimator import CognitiveRegimeEstimator
from arvis.math.control.irg_epsilon_controller import IRGEpsilonController
from arvis.math.control.eps_adaptive import EpsAdaptiveParams
from arvis.cognition.control.temporal_pressure import TemporalPressure
from arvis.cognition.control.temporal_regulation import TemporalRegulation
from arvis.action.action_policy import ActionPolicy
from arvis.kernel.trace.decision_trace import DecisionTrace
from arvis.cognition.conflict.conflict_evaluator import ConflictEvaluator
from arvis.cognition.conflict.default_rules import default_conflict_rules
from arvis.cognition.observability.observability_builder import ObservabilityBuilder
from arvis.cognition.conflict.conflict_pressure_engine import ConflictPressureEngine
from arvis.cognition.coherence.coherence_policy import CoherencePolicy
from arvis.cognition.coherence.coherence_observer import CoherenceObserver
from arvis.stability.stability_state_projector import StabilityStateProjector
from arvis.stability.stability_statistics import StabilityStatistics
from arvis.stability.stability_statistics import StabilityStatsSnapshot
from arvis.cognition.gate.cognitive_gate_result import CognitiveGateResult
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.switching.switching_params import SwitchingParams
from arvis.math.switching.global_stability_observer import GlobalStabilityObserver
from arvis.math.lyapunov.quadratic_lyapunov import make_default_quadratic_family
from arvis.math.switching.switching_runtime import SwitchingRuntime
from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator

from arvis.kernel.pipeline.stages import (
    DecisionStage,
    PassiveContextStage,
    BundleStage,
    ConflictStage,
    CoreStage,
    RegimeStage,
    TemporalStage,
    ConflictModulationStage,
    ControlStage,
    GateStage,
    ControlFeedbackStage,
    StructuralRiskStage,
    ConfirmationStage,
    ExecutionStage,
    ActionStage,
    IntentStage,
    RuntimeStage,
)

DEFAULT_SWITCHING_PARAMS = SwitchingParams(
    alpha=0.15,
    gamma_z=0.4,
    eta=0.05,
    L_T=1.0,
    J=1.5,
)

class PipelineStage(Protocol):
    def run(self, pipeline: "CognitivePipeline", ctx: CognitivePipelineContext) -> None: ...


class CognitivePipeline:

    def __init__(self, core_model: Any | None = None) -> None:
        strict_mode = os.getenv("ARVIS_STRICT_STABILITY", "false").lower() == "true"
        comp = CompositeLyapunov()
        if not comp.check_small_gain(eta=0.05, alpha=0.3, L_T=1.0):
            msg = (
                "Configuration système potentiellement instable : small-gain non satisfait "
                "(ajustez eta, alpha ou L_T)"
            )
            if strict_mode:
                raise RuntimeError(msg)
            else:
                warnings.warn(msg, RuntimeWarning)
        self.decision = DecisionEvaluator()
        self.bundle_builder = CognitiveBundleBuilder()
        self.core = CognitiveCoreEngine(core_model=core_model)

        self.hysteresis = ModeHysteresis()
        self.exploration = ExplorationController()
        self.regime_policy = CognitiveRegimePolicy()

        self.regime_estimator = CognitiveRegimeEstimator()
        self.epsilon_controller = IRGEpsilonController(
            adaptive_params=EpsAdaptiveParams(enabled=True)
        )
        self.temporal_pressure = TemporalPressure()
        self.temporal_regulation = TemporalRegulation()
        self.action_policy = ActionPolicy()
        rules = default_conflict_rules() 
        self.conflict_evaluator = ConflictEvaluator(rules=rules)
        self.observability = ObservabilityBuilder()
        self.conflict_pressure_engine = ConflictPressureEngine()

        self.coherence_observer = CoherenceObserver()
        self.coherence_policy = CoherencePolicy()
        self.control_runtimes: dict[str, CognitiveControlRuntime] = {}
        self.decision_stage = DecisionStage()
        self.passive_stage = PassiveContextStage()
        self.bundle_stage = BundleStage()
        self.conflict_stage = ConflictStage()
        self.core_stage = CoreStage()
        self.regime_stage = RegimeStage()
        self.temporal_stage = TemporalStage()
        self.conflict_modulation_stage = ConflictModulationStage()
        self.control_stage = ControlStage()
        self.gate_stage = GateStage()
        self.control_feedback_stage = ControlFeedbackStage()
        self.structural_risk_stage = StructuralRiskStage()
        self.confirmation_stage = ConfirmationStage()
        self.execution_stage = ExecutionStage()
        self.action_stage = ActionStage()
        self.intent_stage = IntentStage()
        self.runtime_stage = RuntimeStage()
        self.global_stability_observer = GlobalStabilityObserver()
        self.quadratic_lyapunov_family = make_default_quadratic_family(dim=4)
        self.quadratic_comparability = self.quadratic_lyapunov_family.comparability()

        # -----------------------------------------
        # Adaptive stability (M4/M5)
        # -----------------------------------------
        self.adaptive_kappa_estimator = AdaptiveKappaEffEstimator()
        

    def _get_control_runtime(self, user_id: str) -> CognitiveControlRuntime:
        runtime = self.control_runtimes.get(user_id)
        if runtime is None:
            runtime = CognitiveControlRuntime()
            self.control_runtimes[user_id] = runtime
        return runtime
    
    def _safe_run(self, stage: PipelineStage, ctx: CognitivePipelineContext) -> None:
        try:
            stage.run(self, ctx)
        except Exception:
            # fail-soft: never break pipeline
            ctx.extra.setdefault("errors", []).append(
                f"{stage.__class__.__name__}_failure"
            )

    # -----------------------------------------------------
    # PUBLIC API (safe wrapper)
    # -----------------------------------------------------
    def run_from_input(self, input_data: Dict[str, Any]) -> CognitivePipelineResult:
        """
        Public entrypoint for external callers.
        Converts raw input into a pipeline context.
        """
        ctx = CognitivePipelineContext(
            user_id=input_data.get("user_id", "anonymous"),
            cognitive_input=input_data.get("cognitive_input", {}),
        )

        # optional: attach raw input safely
        ctx.extra = getattr(ctx, "extra", {})
        ctx.extra["input_data"] = input_data

        return self.run(ctx)
        
    def run(self, ctx: CognitivePipelineContext) -> CognitivePipelineResult:
        # -----------------------------------------
        # Switching (theorem parameters) 
        # -----------------------------------------
        if getattr(ctx, "switching_params", None) is None:
            ctx.switching_params = DEFAULT_SWITCHING_PARAMS
        if getattr(ctx, "switching_runtime", None) is None:
            ctx.switching_runtime = SwitchingRuntime()
        # Align J with quadratic Lyapunov family comparability
        try:
            comp = getattr(self, "quadratic_comparability", None)
            if comp is not None and getattr(ctx, "switching_params", None) is not None:
                from arvis.math.switching.switching_params import SwitchingParams
                p = ctx.switching_params
                if p is None:
                    p = DEFAULT_SWITCHING_PARAMS
                ctx.switching_params = SwitchingParams(
                    alpha=float(p.alpha),
                    gamma_z=float(p.gamma_z),
                    eta=float(p.eta),
                    L_T=float(p.L_T),
                    J=float(comp.J),
                )
        except Exception:
            pass
        # -----------------------------------------------------
        # 1. DECISION STAGE
        # -----------------------------------------------------
        self._safe_run(self.decision_stage, ctx)

        # -----------------------------------------------------
        # 2. PASSIVE CONTEXT STAGE
        # -----------------------------------------------------
        self._safe_run(self.passive_stage, ctx)

        # -----------------------------------------------------
        # 3. BUNDLE STAGE
        # -----------------------------------------------------
        self._safe_run(self.bundle_stage, ctx)

        # -----------------------------------------------------
        # 4. CONFLICT STAGE
        # -----------------------------------------------------
        self._safe_run(self.conflict_stage, ctx) 

        # -----------------------------------------------------
        # 5. CORE STAGE
        # -----------------------------------------------------
        self._safe_run(self.core_stage, ctx)  

        # -----------------------------------------------------
        # 6. REGIME STAGE
        # -----------------------------------------------------
        self._safe_run(self.regime_stage, ctx)

        # -----------------------------------------------------
        # 7. TEMPORAL STAGE
        # -----------------------------------------------------
        self._safe_run(self.temporal_stage, ctx)

        # -----------------------------------------
        # 8. CONFLICT MODULATION STAGE
        # -----------------------------------------
        self._safe_run(self.conflict_modulation_stage, ctx)

        # -----------------------------------------------------
        # 9. CONTROL STAGE
        # -----------------------------------------------------
        self._safe_run(self.control_stage, ctx)

        # -----------------------------------------------------
        # 10. GATE STAGE
        # -----------------------------------------------------
        self._safe_run(self.gate_stage, ctx)

        # -----------------------------------------
        # 11. CONTROL FEEDBACK STAGE
        # -----------------------------------------
        self._safe_run(self.control_feedback_stage, ctx)

        # -----------------------------------------------------
        # 12. STRUCTURAL RISK STAGE   
        # -----------------------------------------------------
        self._safe_run(self.structural_risk_stage, ctx)

        # -----------------------------------------------------
        # 13. CONFIRMATION STAGE
        # -----------------------------------------------------
        self._safe_run(self.confirmation_stage, ctx)

        # -----------------------------------------------------
        # 14. EXECUTION STAGE
        # -----------------------------------------------------
        self._safe_run(self.execution_stage, ctx)

        requires_confirmation = ctx._requires_confirmation
        can_execute = ctx._can_execute
        assert ctx.execution_status is not None
        execution_status = ctx.execution_status
        # Sync public execution flags into context  
        ctx.requires_confirmation = requires_confirmation
        ctx.can_execute = can_execute

        # -----------------------------------------------------
        # 15. ACTION STAGE
        # -----------------------------------------------------
        self._safe_run(self.action_stage, ctx)

        # -----------------------------------------------------
        # 16. INTENT STAGE
        # -----------------------------------------------------
        self._safe_run(self.intent_stage, ctx)

        # -----------------------------------------------------
        # 17. RUNTIME STAGE
        # -----------------------------------------------------
        self._safe_run(self.runtime_stage, ctx)

        # -----------------------------------------------------
        #  OBSERVABILITY (PURE PROJECTION)
        # -----------------------------------------------------
        obs = self.observability.build(ctx)

        # -----------------------------------------
        #  System Tension 
        # -----------------------------------------
        system_tension = obs.get("system_tension", None)
        if system_tension is not None:
            ctx.extra["system_tension"] = system_tension
            ctx.system_tension = system_tension

        ctx.predictive_snapshot = obs["predictive"]
        ctx.multi_horizon = obs["multi"]
        ctx.global_forecast = obs["forecast"]
        ctx.global_stability = obs["stability"]
        try:
            projector = StabilityStateProjector()
            stats = StabilityStatistics()

            projected = projector.project(ctx.global_stability)
            stability_stats = stats.compute(
                cast(StabilityStatsSnapshot, projected)
            )

            ctx.stability_projection = projected
            ctx.stability_statistics = stability_stats
        except Exception:
            ctx.stability_projection = None
            ctx.stability_statistics = None
        ctx.stability_stats = obs["stats"]

        ctx.symbolic_state = obs["symbolic_state"]
        ctx.symbolic_drift = obs["symbolic_drift"]
        ctx.symbolic_features = obs["symbolic_features"]

        # -----------------------------------------------------
        #  DECISION TRACE (canonical output)
        # -----------------------------------------------------
        if ctx.gate_result is None:
            warnings.warn(
                "gate_result is None → fallback ABSTAIN (vérifiez gate_stage)",
                RuntimeWarning
            )
            ctx.gate_result = LyapunovVerdict.ABSTAIN

        # --- normalize gate_result (strict typing for trace) ---
        if isinstance(ctx.gate_result, LyapunovVerdict):
            normalized_gate_result = CognitiveGateResult.from_lyapunov(
                ctx.gate_result,
                bundle_id=str(getattr(ctx.bundle, "bundle_id", "bundle")),
                reason=str(getattr(ctx.decision_result, "reason", None)),
            )
        else:
            normalized_gate_result = CognitiveGateResult.from_lyapunov(
                LyapunovVerdict.ABSTAIN,
                bundle_id=str(getattr(ctx.bundle, "bundle_id", "bundle")),
                reason="fallback",
            )

        trace = DecisionTrace(
            timestamp=datetime.now(timezone.utc),
            user_id=ctx.user_id,
            gate_result=normalized_gate_result,
            confirmation_request=ctx.confirmation_request,
            confirmation_result=ctx.confirmation_result,
            action_decision=ctx.action_decision,
            executable_intent=ctx.executable_intent,
            conflict=ctx.extra.get("conflict"),
            predictive=ctx.predictive_snapshot,
            stability=ctx.global_stability,
            symbolic=ctx.symbolic_state,
            system_tension=ctx.system_tension,
            quadratic_lyapunov=ctx.quadratic_lyap_snapshot,
            quadratic_comparability=ctx.quadratic_comparability,
            theoretical_regime=ctx.theoretical_regime,
            fast_dynamics=ctx.fast_dynamics,
            perturbation=ctx.perturbation,
            conversation=ctx.conversation_signal,
            governance=ctx.governance,
            pending_actions=ctx.pending_actions,
            events=ctx.events,
            coherence_policy=ctx.coherence_policy,
        )

        # -----------------------------------------
        # Sync canonical context projections
        # -----------------------------------------
        ctx.trace = trace
        ctx.decision = ctx.decision_result
        ctx.control = ctx.control_snapshot

        return CognitivePipelineResult(
            bundle=ctx.bundle,
            decision=ctx.decision_result,
            scientific=ctx.scientific_snapshot,
            control=ctx.control_snapshot,
            gate_result=ctx.gate_result,
            execution_status=execution_status,
            executable_intent=ctx.executable_intent,
            action_decision=ctx.action_decision,
            confirmation_request=ctx.confirmation_request,
            can_execute=can_execute,
            requires_confirmation=requires_confirmation,
            trace=trace,
        )
    

    