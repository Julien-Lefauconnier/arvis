# arvis/kernel/pipeline/cognitive_pipeline_context.py

from dataclasses import dataclass, field
from typing import Any

from arvis.action.action_decision import ActionDecision
from arvis.cognition.bundle.cognitive_bundle_snapshot import (
    CognitiveBundleSnapshot,
)
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import ConfirmationResult
from arvis.cognition.conversation.conversation_context import ConversationContext
from arvis.cognition.conversation.conversation_signal import ConversationSignal
from arvis.cognition.decision.decision_result import DecisionResult
from arvis.cognition.events.base_event import BaseEvent
from arvis.cognition.governance.governance_decision import GovernanceDecision
from arvis.cognition.pending.pending_cognitive_action import PendingCognitiveAction
from arvis.cognition.policy import CognitivePolicyResult
from arvis.errors.base import ArvisError
from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.envelope import CognitiveIREnvelope
from arvis.ir.gate import CognitiveGateIR
from arvis.ir.input import CognitiveInputIR
from arvis.ir.state import CognitiveStateIR
from arvis.kernel.execution.cognitive_execution_state import CognitiveExecutionState
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.kernel.pipeline.context.decision_context import (
    PipelineDecisionContext,
)
from arvis.kernel.pipeline.context.error_context import (
    PipelineErrorContext,
)
from arvis.kernel.pipeline.context.execution_context import (
    PipelineExecutionContext,
)
from arvis.kernel.pipeline.context.observability_context import (
    PipelineObservabilityContext,
)
from arvis.kernel.pipeline.context.projection_context import (
    PipelineProjectionContext,
)
from arvis.kernel.pipeline.context.runtime_bindings_context import (
    PipelineRuntimeBindingsContext,
)
from arvis.kernel.pipeline.context.runtime_policy_context import (
    PipelineRuntimePolicyContext,
)
from arvis.kernel.pipeline.context.scientific_context import (
    PipelineScientificContext,
)
from arvis.kernel.pipeline.context.tooling_context import (
    PipelineToolingContext,
)
from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.trace.decision_trace import DecisionTrace
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.signals import DriftSignal, RiskSignal, UncertaintySignal


@dataclass(kw_only=True)
class CognitivePipelineContext:
    """
    Pure kernel context (ZKCS-safe).

    No service.
    No IO.
    No infra.

    This object only carries already-extracted cognitive inputs and
    intermediate pipeline artifacts.
    """

    user_id: str

    # -------------------------
    # Inputs
    # -------------------------
    cognitive_input: Any
    ir_input: CognitiveInputIR | None = None
    ir_context: CognitiveContextIR | None = None
    long_memory: dict[str, Any] = field(default_factory=dict)
    timeline: list[Any] = field(default_factory=list)
    introspection: Any | None = None
    explanation: Any | None = None
    previous_bundle: Any | None = None
    previous_budget: Any | None = None

    memory_snapshot: Any | None = None
    memory_projection: dict[str, Any] | None = None

    # -------------------------
    # Decision
    # -------------------------
    decision_layer: PipelineDecisionContext = field(
        default_factory=PipelineDecisionContext,
    )

    # -------------------------
    # Scientific bounded context
    # -------------------------
    scientific: PipelineScientificContext = field(
        default_factory=PipelineScientificContext,
    )

    # -------------------------
    # Runtime bindings context
    # -------------------------

    runtime_bindings: PipelineRuntimeBindingsContext = field(
        default_factory=PipelineRuntimeBindingsContext,
    )

    # -------------------------
    # Runtime policy context
    # -------------------------

    runtime_policy: PipelineRuntimePolicyContext = field(
        default_factory=PipelineRuntimePolicyContext,
    )

    # -------------------------
    # Tooling context
    # -------------------------

    tooling: PipelineToolingContext = field(default_factory=PipelineToolingContext)
    # -----------------------------------------------------
    # NOTE(arvis-runtime-v3):
    # # Scientific runtime ownership is now canonicalized under:
    # ctx.scientific.*
    #
    # Root scientific mutable ownership was removed.
    # Compatibility constructor fields remain preserved.
    # - duplicated mutable state
    # - sync drift
    # - legacy mirror inconsistencies
    #
    # Transitional compatibility is now provided exclusively
    # through root-level properties.
    # -----------------------------------------------------

    # -----------------------------------------
    # Global stability enforcement policy
    # "ignore" | "confirm" | "abstain"
    # -----------------------------------------
    global_stability_action: str = "ignore"
    # -------------------------
    # Control layer
    # -------------------------
    control_snapshot: Any | None = None
    control: Any | None = None
    change_budget: Any | None = None

    # -------------------------
    # Gate layer
    # -------------------------
    gate_result: Any | None = None
    ir_gate: CognitiveGateIR | None = None
    ir_projection: Any | None = None
    ir_validity: Any | None = None
    ir_stability: Any | None = None
    ir_adaptive: Any | None = None

    # -------------------------
    # Canonical IR
    # -------------------------
    cognitive_ir: Any | None = None

    # -------------------------
    # IR Serialization / Hash
    # -------------------------
    ir_serialized: dict[str, Any] | None = None
    ir_hash: str | None = None
    ir_envelope: CognitiveIREnvelope | None = None

    # -------------------------
    # Confirmation layer
    # -------------------------
    confirmation_request: ConfirmationRequest | None = None
    confirmation_result: ConfirmationResult | None = None

    # -------------------------
    # Execution layer
    # -------------------------
    execution: PipelineExecutionContext = field(
        default_factory=PipelineExecutionContext,
    )

    # -----------------------------------------------------
    # Legacy compatibility layer
    # -----------------------------------------------------
    # Transitional compatibility input preserved during
    # runtime ownership migration.
    # TODO(arvis-runtime-v2):
    # remove once all callsites migrated to ctx.execution.*
    legacy_execution_state: CognitiveExecutionState | None = field(
        default=None,
        repr=False,
    )

    # -------------------------
    # Errors
    # -------------------------
    error_state: PipelineErrorContext = field(
        default_factory=PipelineErrorContext,
    )

    # -------------------------
    # Extensions
    # -------------------------
    extra: dict[str, Any] = field(default_factory=dict)

    # -------------------------
    # Observability
    # -------------------------
    observability: PipelineObservabilityContext = field(
        default_factory=PipelineObservabilityContext,
    )

    # -----------------------------------------------------
    # Conversation layer (optional, passive)
    # -----------------------------------------------------
    conversation_context: ConversationContext | None = None
    conversation_signal: ConversationSignal | None = None

    # -----------------------------------------------------
    # Governance layer (passive)
    # -----------------------------------------------------
    governance: GovernanceDecision | None = None

    # -----------------------------------------------------
    # Pending (future execution / deferred cognition)
    # -----------------------------------------------------
    pending_actions: list[PendingCognitiveAction] | None = None

    # -----------------------------------------------------
    # Events (cognitive timeline hooks)
    # -----------------------------------------------------
    events: list[BaseEvent] | None = None

    # -----------------------------------------------------
    # Coherence policy (global stability hint)
    # -----------------------------------------------------
    coherence_policy: list[CognitivePolicyResult] | None = None

    # -----------------------------------------------------
    # Canonical trace
    # -----------------------------------------------------
    trace: DecisionTrace | None = None

    # -------------------------
    # Projection (Pi certification)
    # -------------------------
    projection: PipelineProjectionContext = field(
        default_factory=PipelineProjectionContext,
    )
    # -----------------------------------------------------
    # Projection compatibility layer
    # -----------------------------------------------------

    @property
    def runtime_projection(self) -> Any | None:
        return self.projection.runtime_projection

    @runtime_projection.setter
    def runtime_projection(self, value: Any | None) -> None:
        self.projection.runtime_projection = value

    @property
    def structured_projection(self) -> Any | None:
        return self.projection.structured_projection

    @structured_projection.setter
    def structured_projection(self, value: Any | None) -> None:
        self.projection.structured_projection = value

    # -----------------------------------------------------
    # Legacy aliases
    # TODO(arvis-projection-v2):
    # remove once all callsites migrated
    # -----------------------------------------------------

    @property
    def projection_certificate(self) -> Any | None:
        return self.projection.certificate

    @projection_certificate.setter
    def projection_certificate(self, value: Any | None) -> None:
        self.projection.certificate = value

    @property
    def projection_domain_valid(self) -> bool | None:
        return self.projection.domain_valid

    @projection_domain_valid.setter
    def projection_domain_valid(self, value: bool | None) -> None:
        self.projection.domain_valid = value

    @property
    def projection_margin(self) -> float | None:
        return self.projection.margin

    @projection_margin.setter
    def projection_margin(self, value: float | None) -> None:
        self.projection.margin = value

    @property
    def projected_state(self) -> Any | None:
        return self.projection.runtime_projection

    @projected_state.setter
    def projected_state(self, value: Any | None) -> None:
        self.projection.runtime_projection = value

    @property
    def pi_state(self) -> Any | None:
        return self.projection.structured_projection

    @pi_state.setter
    def pi_state(self, value: Any | None) -> None:
        self.projection.structured_projection = value

    @property
    def projection_view(self) -> dict[str, float] | None:
        return self.projection.view

    @projection_view.setter
    def projection_view(self, value: dict[str, float] | None) -> None:
        self.projection.view = value

    @property
    def projection_view_raw(self) -> dict[str, float] | None:
        return self.projection.view_raw

    @projection_view_raw.setter
    def projection_view_raw(self, value: dict[str, float] | None) -> None:
        self.projection.view_raw = value

    # -------------------------
    # Gate overrides
    # -------------------------
    gate_overrides: GateOverrides | None = None

    # -----------------------------------------------------
    # Execution authority projection
    # -----------------------------------------------------
    # Runtime-owned source of truth:
    #   self.execution_state
    #
    # These properties intentionally preserve the public
    # context/result surface while preventing duplicated
    # mutable execution authority inside the context.
    # -----------------------------------------------------

    def __post_init__(self) -> None:
        """
        Transitional compatibility migration hook.
        """
        if self.legacy_execution_state is not None:
            self.execution.execution_state = self.legacy_execution_state

    @property
    def predictive_snapshot(self) -> Any | None:
        return self.observability.projections.predictive_snapshot

    @predictive_snapshot.setter
    def predictive_snapshot(self, value: Any | None) -> None:
        self.observability.projections.predictive_snapshot = value

    @property
    def global_forecast(self) -> Any | None:
        return self.observability.projections.global_forecast

    @global_forecast.setter
    def global_forecast(self, value: Any | None) -> None:
        self.observability.projections.global_forecast = value

    @property
    def global_stability(self) -> Any | None:
        return self.observability.projections.global_stability

    @global_stability.setter
    def global_stability(self, value: Any | None) -> None:
        self.observability.projections.global_stability = value

    @property
    def multi_horizon(self) -> Any | None:
        return self.observability.projections.multi_horizon

    @multi_horizon.setter
    def multi_horizon(self, value: Any | None) -> None:
        self.observability.projections.multi_horizon = value

    @property
    def stability_stats(self) -> Any | None:
        return self.observability.projections.stability_stats

    @stability_stats.setter
    def stability_stats(self, value: Any | None) -> None:
        self.observability.projections.stability_stats = value

    @property
    def stability_projection(self) -> Any | None:
        return self.observability.projections.stability_projection

    @stability_projection.setter
    def stability_projection(self, value: Any | None) -> None:
        self.observability.projections.stability_projection = value

    @property
    def stability_statistics(self) -> Any | None:
        return self.observability.projections.stability_statistics

    @stability_statistics.setter
    def stability_statistics(self, value: Any | None) -> None:
        self.observability.projections.stability_statistics = value

    @property
    def symbolic_drift(self) -> Any | None:
        return self.observability.symbolic.symbolic_drift

    @symbolic_drift.setter
    def symbolic_drift(self, value: Any | None) -> None:
        self.observability.symbolic.symbolic_drift = value

    @property
    def symbolic_features(self) -> Any | None:
        return self.observability.symbolic.symbolic_features

    @symbolic_features.setter
    def symbolic_features(self, value: Any | None) -> None:
        self.observability.symbolic.symbolic_features = value

    @property
    def ir_state(self) -> CognitiveStateIR | None:
        return self.observability.state.ir_state

    @ir_state.setter
    def ir_state(self, value: CognitiveStateIR | None) -> None:
        self.observability.state.ir_state = value

    @property
    def cognitive_state(self) -> Any | None:
        return self.observability.state.cognitive_state

    @cognitive_state.setter
    def cognitive_state(self, value: Any | None) -> None:
        self.observability.state.cognitive_state = value

    @property
    def system_tension(self) -> Any | None:
        return self.observability.diagnostics.system_tension

    @system_tension.setter
    def system_tension(self, value: Any | None) -> None:
        self.observability.diagnostics.system_tension = value

    def _ensure_execution_state(
        self,
    ) -> CognitiveExecutionState:
        if self.execution.execution_state is None:
            self.execution.execution_state = CognitiveExecutionState()

        return self.execution.execution_state

    @property
    def executable_intent(self) -> Any | None:
        return self.execution.executable_intent

    @executable_intent.setter
    def executable_intent(
        self,
        value: Any | None,
    ) -> None:
        self.execution.executable_intent = value

    @property
    def action_decision(
        self,
    ) -> ActionDecision | None:
        return self.execution.action_decision

    @action_decision.setter
    def action_decision(
        self,
        value: ActionDecision | None,
    ) -> None:
        self.execution.action_decision = value

    @property
    def execution_state(
        self,
    ) -> CognitiveExecutionState | None:
        return self.execution.execution_state

    @execution_state.setter
    def execution_state(
        self,
        value: CognitiveExecutionState | None,
    ) -> None:
        self.execution.execution_state = value

    # Legacy projection properties
    @property
    def can_execute(self) -> bool:
        return self._ensure_execution_state().can_execute

    @can_execute.setter
    def can_execute(self, value: bool) -> None:
        self._ensure_execution_state().can_execute = value

    @property
    def requires_confirmation(self) -> bool:
        return self._ensure_execution_state().requires_confirmation

    @requires_confirmation.setter
    def requires_confirmation(self, value: bool) -> None:
        self._ensure_execution_state().requires_confirmation = value

    @property
    def execution_status(self) -> ExecutionGateStatus | None:
        return self._ensure_execution_state().execution_status

    @execution_status.setter
    def execution_status(
        self,
        value: ExecutionGateStatus | None,
    ) -> None:
        self._ensure_execution_state().execution_status = value

    # -----------------------------------------------------
    # Decision compatibility layer
    # -----------------------------------------------------

    @property
    def decision_result(self) -> DecisionResult | None:
        return self.decision_layer.decision_result

    @decision_result.setter
    def decision_result(self, value: DecisionResult | None) -> None:
        self.decision_layer.decision_result = value

    @property
    def ir_decision(self) -> CognitiveDecisionIR | None:
        return self.decision_layer.ir_decision

    @ir_decision.setter
    def ir_decision(self, value: CognitiveDecisionIR | None) -> None:
        self.decision_layer.ir_decision = value

    @property
    def bundle(self) -> CognitiveBundleSnapshot | None:
        return self.decision_layer.bundle

    @bundle.setter
    def bundle(self, value: CognitiveBundleSnapshot | None) -> None:
        self.decision_layer.bundle = value

    # -----------------------------------------------------
    # Canonical scientific compatibility properties
    # -----------------------------------------------------
    @property
    def collapse_risk(
        self,
    ) -> RiskSignal | float:
        return self.scientific.core.collapse_risk

    @collapse_risk.setter
    def collapse_risk(
        self,
        value: RiskSignal | float,
    ) -> None:
        self.scientific.core.collapse_risk = value

    @property
    def uncertainty(
        self,
    ) -> UncertaintySignal | float | None:
        return self.scientific.core.uncertainty

    @uncertainty.setter
    def uncertainty(
        self,
        value: UncertaintySignal | float | None,
    ) -> None:
        self.scientific.core.uncertainty = value

    @property
    def drift_score(
        self,
    ) -> DriftSignal | float:
        return self.scientific.core.drift_score

    @drift_score.setter
    def drift_score(
        self,
        value: DriftSignal | float,
    ) -> None:
        self.scientific.core.drift_score = value

    @property
    def prev_lyap(self) -> LyapunovState | float | None:
        return self.scientific.lyapunov.prev_lyap

    @prev_lyap.setter
    def prev_lyap(self, value: LyapunovState | None) -> None:
        self.scientific.lyapunov.prev_lyap = value

    @property
    def cur_lyap(self) -> LyapunovState | float | None:
        return self.scientific.lyapunov.cur_lyap

    @cur_lyap.setter
    def cur_lyap(self, value: LyapunovState | None) -> None:
        self.scientific.lyapunov.cur_lyap = value

    @property
    def stable(self) -> bool | None:
        return self.scientific.regime_state.stable

    @stable.setter
    def stable(self, value: bool | None) -> None:
        self.scientific.regime_state.stable = value

    @property
    def delta_w(self) -> float | None:
        return self.scientific.composite.delta_w

    @delta_w.setter
    def delta_w(self, value: float | None) -> None:
        self.scientific.composite.delta_w = value

    @property
    def adaptive_snapshot(self) -> AdaptiveSnapshot | None:
        return self.scientific.adaptive.adaptive_snapshot

    @adaptive_snapshot.setter
    def adaptive_snapshot(
        self,
        value: AdaptiveSnapshot | None,
    ) -> None:
        self.scientific.adaptive.adaptive_snapshot = value

    # -----------------------------------------------------
    # Transitional scientific compatibility properties
    # -----------------------------------------------------

    @property
    def switching_params(self) -> Any | None:
        return self.scientific.switching.switching_params

    @switching_params.setter
    def switching_params(self, value: Any | None) -> None:
        self.scientific.switching.switching_params = value

    @property
    def switching_runtime(self) -> Any | None:
        return self.scientific.switching.switching_runtime

    @switching_runtime.setter
    def switching_runtime(self, value: Any | None) -> None:
        self.scientific.switching.switching_runtime = value

    @property
    def switching_safe(self) -> bool | None:
        return self.scientific.switching.switching_safe

    @switching_safe.setter
    def switching_safe(
        self,
        value: bool | None,
    ) -> None:
        self.scientific.switching.switching_safe = value

    @property
    def switching_metrics(
        self,
    ) -> dict[str, Any]:
        return self.scientific.switching.switching_metrics

    @switching_metrics.setter
    def switching_metrics(
        self,
        value: dict[str, Any],
    ) -> None:
        self.scientific.switching.switching_metrics = value

    @property
    def symbolic_state(self) -> Any | None:
        return self.scientific.lyapunov.symbolic_state

    @symbolic_state.setter
    def symbolic_state(self, value: Any | None) -> None:
        self.scientific.lyapunov.symbolic_state = value

    @property
    def symbolic_state_prev(self) -> Any | None:
        return self.scientific.lyapunov.symbolic_state_prev

    @symbolic_state_prev.setter
    def symbolic_state_prev(self, value: Any | None) -> None:
        self.scientific.lyapunov.symbolic_state_prev = value

    @property
    def slow_state(self) -> Any | None:
        return self.scientific.lyapunov.slow_state

    @slow_state.setter
    def slow_state(self, value: Any | None) -> None:
        self.scientific.lyapunov.slow_state = value

    @property
    def slow_state_prev(self) -> Any | None:
        return self.scientific.lyapunov.slow_state_prev

    @slow_state_prev.setter
    def slow_state_prev(self, value: Any | None) -> None:
        self.scientific.lyapunov.slow_state_prev = value

    @property
    def fast_dynamics(self) -> Any | None:
        return self.scientific.regime_state.fast_dynamics

    @fast_dynamics.setter
    def fast_dynamics(self, value: Any | None) -> None:
        self.scientific.regime_state.fast_dynamics = value

    @property
    def perturbation(self) -> Any | None:
        return self.scientific.regime_state.perturbation

    @perturbation.setter
    def perturbation(self, value: Any | None) -> None:
        self.scientific.regime_state.perturbation = value

    @property
    def theoretical_regime(self) -> Any | None:
        return self.scientific.regime_state.theoretical_regime

    @theoretical_regime.setter
    def theoretical_regime(self, value: Any | None) -> None:
        self.scientific.regime_state.theoretical_regime = value

    @property
    def quadratic_lyap_snapshot(self) -> Any | None:
        return self.scientific.lyapunov.quadratic_lyap_snapshot

    @quadratic_lyap_snapshot.setter
    def quadratic_lyap_snapshot(self, value: Any | None) -> None:
        self.scientific.lyapunov.quadratic_lyap_snapshot = value

    @property
    def quadratic_comparability(self) -> Any | None:
        return self.scientific.lyapunov.quadratic_comparability

    @quadratic_comparability.setter
    def quadratic_comparability(self, value: Any | None) -> None:
        self.scientific.lyapunov.quadratic_comparability = value

    @property
    def scientific_snapshot(self) -> Any | None:
        return self.scientific.core.scientific_snapshot

    @scientific_snapshot.setter
    def scientific_snapshot(self, value: Any | None) -> None:
        self.scientific.core.scientific_snapshot = value

    @property
    def w_prev(self) -> float | None:
        return self.scientific.composite.w_prev

    @w_prev.setter
    def w_prev(self, value: float | None) -> None:
        self.scientific.composite.w_prev = value

    @property
    def w_current(self) -> float | None:
        return self.scientific.composite.w_current

    @w_current.setter
    def w_current(self, value: float | None) -> None:
        self.scientific.composite.w_current = value

    @property
    def delta_w_history(self) -> list[float]:
        return self.scientific.composite.delta_w_history

    @delta_w_history.setter
    def delta_w_history(self, value: list[float]) -> None:
        self.scientific.composite.delta_w_history = value

    @property
    def regime(self) -> str | None:
        return self.scientific.regime_state.regime

    @regime.setter
    def regime(self, value: str | None) -> None:
        self.scientific.regime_state.regime = value

    @property
    def global_stability_metrics(self) -> Any | None:
        return self.scientific.adaptive.global_stability_metrics

    @global_stability_metrics.setter
    def global_stability_metrics(self, value: Any | None) -> None:
        self.scientific.adaptive.global_stability_metrics = value

    @property
    def validity_envelope(self) -> Any | None:
        return self.scientific.adaptive.validity_envelope

    @validity_envelope.setter
    def validity_envelope(self, value: Any | None) -> None:
        self.scientific.adaptive.validity_envelope = value

    @property
    def use_paper_slow_dynamics(self) -> bool:
        return self.scientific.adaptive.use_paper_slow_dynamics

    @use_paper_slow_dynamics.setter
    def use_paper_slow_dynamics(self, value: bool) -> None:
        self.scientific.adaptive.use_paper_slow_dynamics = value

    # -----------------------------------------------------
    # Error compatibility layer
    # -----------------------------------------------------

    @property
    def errors(self) -> list[ArvisError]:
        return self.error_state.errors

    # -------------------------
    # Runtime
    # -------------------------
    @property
    def control_runtime(self) -> Any | None:
        return self.runtime_bindings.control_runtime

    @control_runtime.setter
    def control_runtime(self, value: Any | None) -> None:
        self.runtime_bindings.control_runtime = value

    @property
    def _tool_success(self) -> bool | None:
        return self.tooling.tool_success

    @_tool_success.setter
    def _tool_success(self, value: bool | None) -> None:
        self.tooling.tool_success = value

    @property
    def _tool_failure(self) -> bool | None:
        return self.tooling.tool_failure

    @_tool_failure.setter
    def _tool_failure(self, value: bool | None) -> None:
        self.tooling.tool_failure = value

    @property
    def _last_tool_spec(self) -> Any | None:
        return self.tooling.last_tool_spec

    @_last_tool_spec.setter
    def _last_tool_spec(self, value: Any | None) -> None:
        self.tooling.last_tool_spec = value

    @property
    def force_tool(self) -> str | None:
        return self.runtime_policy.force_tool

    @force_tool.setter
    def force_tool(self, value: str | None) -> None:
        self.runtime_policy.force_tool = value

    @property
    def _force_execution(self) -> bool:
        return self.runtime_policy.force_execution

    @_force_execution.setter
    def _force_execution(self, value: bool) -> None:
        self.runtime_policy.force_execution = value

    @property
    def retry_tool(self) -> bool:
        return self.runtime_policy.retry_requested

    @retry_tool.setter
    def retry_tool(self, value: bool) -> None:
        self.runtime_policy.retry_requested = value

    @property
    def tool_retry_count(self) -> int:
        return self.runtime_policy.retry_count

    @tool_retry_count.setter
    def tool_retry_count(self, value: int) -> None:
        self.runtime_policy.retry_count = value
