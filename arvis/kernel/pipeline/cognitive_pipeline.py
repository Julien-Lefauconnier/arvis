# arvis/kernel/pipeline/cognitive_pipeline.py

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import replace
import os
import warnings
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from typing import Any, cast, Protocol, Dict, Iterable, Iterator

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.pipeline.cognitive_pipeline_result import CognitivePipelineResult

from arvis.cognition.decision.decision_evaluator import DecisionEvaluator
from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder
from arvis.cognition.core.cognitive_core_engine import CognitiveCoreEngine


from arvis.cognition.control.mode_hysteresis import ModeHysteresis
from arvis.cognition.control.exploration_controller import ExplorationController
from arvis.cognition.control.regime_policy import CognitiveRegimePolicy
from arvis.cognition.control.cognitive_control_runtime import CognitiveControlRuntime
from arvis.cognition.gate.reason_code_normalizer import ReasonCodeNormalizer
from arvis.cognition.gate.gate_trace_builder import GateTraceBuilder

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
from arvis.cognition.state.cognitive_state_builder import CognitiveStateBuilder
from arvis.adapters.ir.gate_adapter import GateIRAdapter
from arvis.adapters.ir.state_adapter import StateIRAdapter
from arvis.adapters.ir.projection_adapter import ProjectionIRAdapter
from arvis.adapters.ir.validity_adapter import ValidityIRAdapter
from arvis.adapters.ir.stability_adapter import StabilityIRAdapter
from arvis.adapters.ir.adaptive_adapter import AdaptiveIRAdapter
from arvis.adapters.ir.cognitive_ir_builder import CognitiveIRBuilder
from arvis.ir.input import CognitiveInputIR
from arvis.ir.context import CognitiveContextIR
from arvis.ir.envelope import CognitiveIREnvelope
from arvis.ir.cognitive_ir import CognitiveIR
from arvis.ir.serialization.cognitive_ir_serializer import CognitiveIRSerializer
from arvis.ir.serialization.cognitive_ir_hasher import CognitiveIRHasher
from arvis.ir.validation.cognitive_ir_validator import CognitiveIRValidator
from arvis.ir.normalization.cognitive_ir_normalizer import CognitiveIRNormalizer
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.switching.switching_params import SwitchingParams
from arvis.math.switching.global_stability_observer import GlobalStabilityObserver
from arvis.math.lyapunov.quadratic_lyapunov import make_default_quadratic_family
from arvis.math.switching.switching_runtime import SwitchingRuntime
from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator
from arvis.kernel.projection.domain import ProjectionDomain, NumericBounds
from arvis.kernel.projection.validator import ProjectionValidator
from arvis.kernel.projection.pi_impl import PiImpl
from arvis.math.projection.pi_operator import PiOperator

from arvis.kernel.pipeline.stages import (
    ToolFeedbackStage,
    ToolRetryStage,
    DecisionStage,
    PassiveContextStage,
    BundleStage,
    ConflictStage,
    CoreStage,
    RegimeStage,
    TemporalStage,
    ConflictModulationStage,
    ControlStage,
    ProjectionStage,
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
                "Potentially unstable system configuration: small-gain not satisfied"
                "(adjust eta, alpha or L_T)"
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
        self.tool_feedback_stage = ToolFeedbackStage()
        self.tool_retry_stage = ToolRetryStage()
        self.decision_stage = DecisionStage()
        self.passive_stage = PassiveContextStage()
        self.bundle_stage = BundleStage()
        self.conflict_stage = ConflictStage()
        self.core_stage = CoreStage()
        self.regime_stage = RegimeStage()
        self.temporal_stage = TemporalStage()
        self.conflict_modulation_stage = ConflictModulationStage()
        self.control_stage = ControlStage()
        self.projection_stage = ProjectionStage()
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
        self.tool_executor = None

        # -----------------------------------------
        # Adaptive stability (M4/M5)
        # -----------------------------------------
        self.adaptive_kappa_estimator = AdaptiveKappaEffEstimator()

        # -----------------------------------------
        # Projection domain (Pi validation)
        # -----------------------------------------
        self.pi_impl = PiImpl()
        self.pi_operator = PiOperator()

        self.projection_domain = ProjectionDomain(
            bounds={
                "state.system_tension": NumericBounds(0.0, 100.0),

                # extensions safe Π_impl
                "state.coherence_score": NumericBounds(0.0, 1.0),
                "risk.conflict_pressure": NumericBounds(0.0, 100.0),
                "control.control_signal": NumericBounds(0.0, 100.0),
                "trace.adaptive_kappa_eff": NumericBounds(0.0, 1.0),
            },
            max_payload_size=10000,
        )
        self.projection_validator = ProjectionValidator(self.projection_domain)


    # -----------------------------------------------------
    # ITERATIVE PIPELINE SUPPORT (non-breaking)
    # -----------------------------------------------------
    def iter_stages(self) -> Iterable[PipelineStage]:
        """
        Ordered list of pipeline stages.
        Single source of truth for execution order.
        """
        return [
            self.tool_feedback_stage,
            self.tool_retry_stage,
            self.decision_stage,
            self.passive_stage,
            self.bundle_stage,
            self.conflict_stage,
            self.core_stage,
            self.regime_stage,
            self.temporal_stage,
            self.conflict_modulation_stage,
            self.control_stage,
            self.projection_stage,
            self.gate_stage,
            self.control_feedback_stage,
            self.structural_risk_stage,
            self.confirmation_stage,
            self.execution_stage,
            self.action_stage,
            self.intent_stage,
            self.runtime_stage,
        ]


    def _get_control_runtime(self, user_id: str) -> CognitiveControlRuntime:
        runtime = self.control_runtimes.get(user_id)
        if runtime is None:
            runtime = CognitiveControlRuntime()
            self.control_runtimes[user_id] = runtime
        return runtime
    
    def _safe_run(self, stage: PipelineStage, ctx: CognitivePipelineContext) -> None:
        try:
            stage.run(self, ctx)
        except Exception as e:
            ctx.extra.setdefault("errors", []).append({
                "stage": stage.__class__.__name__,
                "error": str(e),
                "type": type(e).__name__,
            })

    def _bootstrap_ir_input(self, ctx: CognitivePipelineContext) -> None:
        if getattr(ctx, "ir_input", None) is not None:
            return

        cognitive_input = getattr(ctx, "cognitive_input", None)
        metadata: Dict[str, Any] = (
            dict(cognitive_input) if isinstance(cognitive_input, dict) else {}
        )

        ctx.ir_input = CognitiveInputIR(
            input_id=str(metadata.get("input_id", f"input::{ctx.user_id}")),
            actor_id=str(metadata.get("actor_id", ctx.user_id)),
            surface_kind=str(metadata.get("surface_kind", "unknown")),
            intent_hint=metadata.get("intent_hint"),
            metadata=metadata,
        )

    def _bootstrap_ir_context(self, ctx: CognitivePipelineContext) -> None:
        if getattr(ctx, "ir_context", None) is not None:
            return

        long_memory = getattr(ctx, "long_memory", {}) or {}
        constraints = tuple(long_memory.get("constraints", []) or [])
        preferences = long_memory.get("preferences", {}) or {}
        conversation_mode = None

        conversation_context = getattr(ctx, "conversation_context", None)
        if conversation_context is not None:
            conversation_mode = getattr(conversation_context, "mode", None)

        if conversation_mode is None:
            conversation_mode = getattr(ctx, "extra", {}).get("conversation_mode")

        if conversation_mode is not None:
            conversation_mode = str(getattr(conversation_mode, "value", conversation_mode))

        ctx.ir_context = CognitiveContextIR(
            user_id=ctx.user_id,
            session_id=getattr(ctx, "extra", {}).get("session_id"),
            conversation_mode=conversation_mode,
            long_memory_constraints=constraints,
            long_memory_preferences=preferences,
            extra={},
        )
    
    def _refresh_ir_context_extra(self, ctx: CognitivePipelineContext) -> None:
        ir_context = ctx.ir_context
        if ir_context is None:
            return

        current_extra = dict(ir_context.extra or {})

        propagated_keys = (
            "confirmation_override",
        )

        for key in propagated_keys:
            if key in ctx.extra:
                current_extra[key] = ctx.extra[key]

        ctx.ir_context = replace(ir_context, extra=current_extra)
    
    def _prepare_run(self, ctx: CognitivePipelineContext) -> None:
        if ctx.extra.get("__pipeline_prepared", False):
            return

        self._bootstrap_ir_input(ctx)
        self._bootstrap_ir_context(ctx)

        if getattr(ctx, "switching_params", None) is None:
            ctx.switching_params = DEFAULT_SWITCHING_PARAMS
        if getattr(ctx, "switching_runtime", None) is None:
            ctx.switching_runtime = SwitchingRuntime()

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

        ctx.extra["__pipeline_prepared"] = True

    def _sync_execution_flags(self, ctx: CognitivePipelineContext) -> None:
        requires_confirmation = ctx._requires_confirmation
        can_execute = ctx._can_execute
        assert ctx.execution_status is not None
        ctx.requires_confirmation = requires_confirmation
        ctx.can_execute = can_execute

    def run_stage(
        self,
        ctx: CognitivePipelineContext,
        stage: PipelineStage
    ) -> None:
        self._prepare_run(ctx)
        self._safe_run(stage, ctx)
        if stage is self.execution_stage:
            self._sync_execution_flags(ctx)


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
            long_memory=input_data.get("long_memory", {}) or {},
            timeline=input_data.get("timeline", []) or [],
            introspection=input_data.get("introspection"),
        )

        # optional: attach raw input safely
        ctx.extra = getattr(ctx, "extra", {})
        ctx.extra["input_data"] = input_data
        if "session_id" in input_data:
            ctx.extra["session_id"] = input_data["session_id"]
        if "conversation_mode" in input_data:
            ctx.extra["conversation_mode"] = input_data["conversation_mode"]

        self._bootstrap_ir_input(ctx)
        self._bootstrap_ir_context(ctx)

        return self.run(ctx)
        
    def run(self, ctx: CognitivePipelineContext) -> CognitivePipelineResult:
        self._prepare_run(ctx)
        for stage in self.iter_stages():
            self.run_stage(ctx, stage)
        return self.finalize_run(ctx)

    def run_iter(self, ctx: CognitivePipelineContext) -> Iterator[PipelineStage]:
        self._prepare_run(ctx)
        for stage in self.iter_stages():
            self.run_stage(ctx, stage)
            yield stage

    def finalize_run(self, ctx: CognitivePipelineContext) -> CognitivePipelineResult:
        if ctx.extra.get("__pipeline_finalized", False):
            cached = ctx.extra.get("__pipeline_result")
            if cached is not None:
                return cast(CognitivePipelineResult, cached)
        requires_confirmation = ctx.requires_confirmation
        can_execute = ctx.can_execute
        assert ctx.execution_status is not None
        execution_status = ctx.execution_status

        # -----------------------------------------------------
        #  OBSERVABILITY (PURE PROJECTION)
        # -----------------------------------------------------
        obs = self.observability.build(ctx)

        # -----------------------------------------
        #  System Tension (extracted early for projection)
        # -----------------------------------------
        system_tension = obs.get("system_tension", None)
        if system_tension is not None:
            ctx.extra["system_tension"] = system_tension
            ctx.system_tension = system_tension

        # -----------------------------------------------------
        # POST-OBSERVABILITY PROJECTION REFRESH
        # -----------------------------------------------------
        try:
            self.projection_stage.refresh(self, ctx)
        except Exception:
            ctx.extra.setdefault("errors", []).append("projection_refresh_failure")

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

        gate_decision_trace = GateTraceBuilder.build(
            tuple(ctx.extra.get("verdict_transition_trace", []) or ())
        )

        # --- normalize gate_result (strict typing for trace) ---
        raw_reason_codes = ctx.extra.get("final_reason_codes", ()) or ()

        final_reason_codes = ReasonCodeNormalizer.normalize(raw_reason_codes)

        if isinstance(ctx.gate_result, LyapunovVerdict):
            normalized_gate_result = CognitiveGateResult.from_lyapunov(
                ctx.gate_result,
                bundle_id=str(getattr(ctx.bundle, "bundle_id", "bundle")),
                reason_codes=final_reason_codes,
                decision_trace=gate_decision_trace,
            )
        else:
            normalized_gate_result = CognitiveGateResult.from_lyapunov(
                LyapunovVerdict.ABSTAIN,
                bundle_id=str(getattr(ctx.bundle, "bundle_id", "bundle")),
                reason_codes=final_reason_codes or ("fallback_abstain",),
                decision_trace=gate_decision_trace,
            )
        
        try:
            ctx.ir_gate = GateIRAdapter.from_gate(normalized_gate_result)
        except Exception:
            ctx.extra.setdefault("errors", []).append("gate_ir_adapter_failure")
            ctx.ir_gate = None
        
        # -----------------------------------------------------
        # IR (projection / validity / stability / adaptive)
        # -----------------------------------------------------
        try:
            ctx.ir_projection = ProjectionIRAdapter.from_projection(
                getattr(ctx, "projection_certificate", None)
            )
        except Exception:
            ctx.ir_projection = None
            ctx.extra.setdefault("errors", []).append("projection_ir_adapter_failure")

        try:
            ctx.ir_validity = ValidityIRAdapter.from_validity(
                getattr(ctx, "validity_envelope", None)
            )
        except Exception:
            ctx.ir_validity = None
            ctx.extra.setdefault("errors", []).append("validity_ir_adapter_failure")

        try:
            ctx.ir_stability = StabilityIRAdapter.from_stability(
                getattr(ctx, "stability_projection", None)
            )
        except Exception:
            ctx.ir_stability = None
            ctx.extra.setdefault("errors", []).append("stability_ir_adapter_failure")

        try:
            ctx.ir_adaptive = AdaptiveIRAdapter.from_adaptive(
                getattr(ctx, "adaptive_snapshot", None)
            )
        except Exception:
            ctx.ir_adaptive = None
            ctx.extra.setdefault("errors", []).append("adaptive_ir_adapter_failure")
        
        # -----------------------------------------------------
        # IR CONTEXT REFRESH (propagate late pipeline flags)
        # -----------------------------------------------------
        try:
            self._refresh_ir_context_extra(ctx)
        except Exception:
            ctx.extra.setdefault("errors", []).append("ir_context_refresh_failure")
        
        # -----------------------------------------------------
        # COGNITIVE IR (canonical aggregation)
        # -----------------------------------------------------
        try:
            ctx.cognitive_ir = CognitiveIRBuilder.from_context(ctx)
        except Exception:
            ctx.cognitive_ir = None
            ctx.extra.setdefault("errors", []).append("cognitive_ir_build_failure")

        if ctx.cognitive_ir is not None:
            ir = CognitiveIRNormalizer.normalize(ctx.cognitive_ir)
            ctx.cognitive_ir = ir

        # -----------------------------------------------------
        # IR VALIDATION
        # -----------------------------------------------------
        try:
            if ctx.cognitive_ir is not None:
                CognitiveIRValidator.validate(ctx.cognitive_ir)
        except Exception:
            ctx.extra.setdefault("errors", []).append("cognitive_ir_validation_failure")
            raise

        # -----------------------------------------------------
        # IR SERIALIZATION + HASH (canonical)
        # -----------------------------------------------------
        try:
            if ctx.cognitive_ir is not None:
                ctx.ir_serialized = CognitiveIRSerializer.to_canonical_dict(ctx.cognitive_ir)
                ctx.ir_hash = CognitiveIRHasher.hash(ctx.cognitive_ir)
                ctx.ir_envelope = CognitiveIREnvelope.build(
                    ir=ctx.cognitive_ir,
                    serialized=ctx.ir_serialized,
                    hash_value=ctx.ir_hash,
                )
            else:
                ctx.ir_serialized = None
                ctx.ir_hash = None
                ctx.ir_envelope = None
        except Exception:
            ctx.ir_serialized = None
            ctx.ir_hash = None
            ctx.ir_envelope = None
            ctx.extra.setdefault("errors", []).append("ir_serialization_failure")

        # -----------------------------------------------------
        # TRACE (must exist BEFORE state)
        # -----------------------------------------------------
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

        ctx.trace = trace

        # -----------------------------------------------------
        # COGNITIVE STATE (canonical)
        # -----------------------------------------------------
        try:
            ctx.cognitive_state = CognitiveStateBuilder.from_context(ctx)
        except Exception:
            ctx.cognitive_state = None
            ctx.extra.setdefault("errors", []).append("cognitive_state_build_failure")

        # -----------------------------------------------------
        # CONTRACT VALIDATION (critical)
        # -----------------------------------------------------
        try:
            if ctx.cognitive_state is not None:
                from arvis.contracts.cognitive_state_contract import CognitiveStateContract

                CognitiveStateContract.validate(ctx.cognitive_state)
        except Exception:
            ctx.extra.setdefault("errors", []).append("cognitive_state_contract_failure")
            ctx.cognitive_state = None

        # -----------------------------------------------------
        # STATE IR (export from canonical state)
        # -----------------------------------------------------
        try:
            if ctx.cognitive_state is not None:
                ctx.ir_state = StateIRAdapter.from_state(ctx.cognitive_state)
            else:
                ctx.ir_state = None
        except Exception:
            ctx.extra.setdefault("errors", []).append("state_ir_adapter_failure")
            ctx.ir_state = None

        # -----------------------------------------
        # Sync canonical context projections
        # -----------------------------------------
        
        ctx.decision = ctx.decision_result
        ctx.control = ctx.control_snapshot

        result = CognitivePipelineResult(
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
            ir_input=ctx.ir_input,
            ir_context=ctx.ir_context,
            ir_decision=ctx.ir_decision,
            ir_state=ctx.ir_state,
            ir_gate=ctx.ir_gate,
            ir_projection=ctx.ir_projection,
            ir_validity=ctx.ir_validity,
            ir_stability=ctx.ir_stability,
            ir_adaptive=ctx.ir_adaptive,
            cognitive_ir=ctx.cognitive_ir,
            ir_serialized=ctx.ir_serialized,
            ir_hash=ctx.ir_hash,
            ir_envelope=ctx.ir_envelope,
            cognitive_state=ctx.cognitive_state,
        )
        ctx.extra["__pipeline_finalized"] = True
        ctx.extra["__pipeline_result"] = result

        return result
    

    def run_from_ir(self, ir: CognitiveIR) -> CognitivePipelineResult:
        """
        Replay pipeline from canonical IR (deterministic mode).
        """
        if ir.context is None:
            raise ValueError("Cannot replay from IR without context")

        if ir.input is None:
            raise ValueError("Cannot replay from IR without input")

        ctx = CognitivePipelineContext(
            user_id=ir.context.user_id,
            cognitive_input=ir.input.metadata,
        )

        ctx.ir_input = ir.input
        ctx.ir_context = ir.context
        ctx.cognitive_ir = ir
        ctx.extra["replay_mode"] = True

        return self.run(ctx)
