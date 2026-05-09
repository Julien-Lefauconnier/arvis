# arvis/kernel/pipeline/cognitive_pipeline_context.py

from dataclasses import InitVar, dataclass, field
from typing import Any

from arvis.action.action_decision import ActionDecision
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import ConfirmationResult
from arvis.cognition.conversation.conversation_context import ConversationContext
from arvis.cognition.conversation.conversation_signal import ConversationSignal
from arvis.cognition.events.base_event import BaseEvent
from arvis.cognition.governance.governance_decision import GovernanceDecision
from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState
from arvis.cognition.pending.pending_cognitive_action import PendingCognitiveAction
from arvis.cognition.policy import CognitivePolicyResult
from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.envelope import CognitiveIREnvelope
from arvis.ir.gate import CognitiveGateIR
from arvis.ir.input import CognitiveInputIR
from arvis.ir.state import CognitiveStateIR
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.kernel.pipeline.context.decision_context import (
    PipelineDecisionContext,
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
from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.trace.decision_trace import DecisionTrace
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.signals import DriftSignal, RiskSignal, UncertaintySignal
from arvis.math.stability.validity_envelope import ValidityEnvelope
from arvis.math.switching.switching_runtime import SwitchingRuntime
from arvis.runtime.execution.cognitive_execution_state import (
    CognitiveExecutionState,
)


@dataclass
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
    # Scientific / core layer
    # -------------------------
    scientific_snapshot: Any | None = None
    collapse_risk: RiskSignal | float = 0.0
    uncertainty: UncertaintySignal | float | None = None
    # Fast Lyapunov state (x)
    prev_lyap: LyapunovState | None = None
    cur_lyap: LyapunovState | None = None
    prev_quadratic_lyap_state: Any | None = None
    cur_quadratic_lyap_state: Any | None = None
    quadratic_lyap_snapshot: Any | None = None
    quadratic_comparability: Any | None = None
    # Slow state (z)
    slow_state: SlowState | None = None
    slow_state_prev: SlowState | None = None
    # Symbolic state (used for T(x))
    symbolic_state: SymbolicState | None = None
    symbolic_state_prev: SymbolicState | None = None
    # Composite Lyapunov tracking
    w_current: float | None = None
    w_prev: float | None = None
    delta_w: float | None = None

    drift_score: DriftSignal | float = 0.0
    regime: str | None = None
    stable: bool | None = None
    regime_confidence: float = 0.0
    theoretical_regime: Any | None = None
    fast_dynamics: Any | None = None
    perturbation: Any | None = None

    # -------------------------
    # Switching runtime (theorem)
    # -------------------------
    switching_runtime: SwitchingRuntime | None = None
    switching_params: Any | None = None
    switching_safe: bool | None = None
    switching_metrics: dict[str, Any] = field(default_factory=dict)
    # -------------------------
    # Adaptive stability (canonical)
    # -------------------------
    adaptive_snapshot: AdaptiveSnapshot | None = None
    validity_envelope: ValidityEnvelope | None = None

    use_paper_slow_dynamics: bool = False
    use_paper_composite_gate: bool = False
    global_stability_metrics: Any | None = None
    enforce_global_stability: bool = False
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
    # Extensions
    # -------------------------
    extra: dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------
    # Transitional observability constructor compatibility
    # -----------------------------------------------------

    predictive_snapshot_init: InitVar[Any | None] = None
    global_forecast_init: InitVar[Any | None] = None
    global_stability_init: InitVar[Any | None] = None
    multi_horizon_init: InitVar[Any | None] = None

    stability_stats_init: InitVar[Any | None] = None
    stability_projection_init: InitVar[Any | None] = None
    stability_statistics_init: InitVar[Any | None] = None

    symbolic_drift_init: InitVar[Any | None] = None
    symbolic_features_init: InitVar[Any | None] = None

    system_tension: Any | None = None

    ir_state_init: InitVar[CognitiveStateIR | None] = None
    cognitive_state_init: InitVar[Any | None] = None

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

    # -------------------------
    # Runtime
    # -------------------------
    control_runtime: Any | None = None

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

    def __post_init__(
        self,
        predictive_snapshot_init: Any | None,
        global_forecast_init: Any | None,
        global_stability_init: Any | None,
        multi_horizon_init: Any | None,
        stability_stats_init: Any | None,
        stability_projection_init: Any | None,
        stability_statistics_init: Any | None,
        symbolic_drift_init: Any | None,
        symbolic_features_init: Any | None,
        ir_state_init: CognitiveStateIR | None,
        cognitive_state_init: Any | None,
    ) -> None:
        """
        Transitional compatibility migration hook.
        """
        if self.legacy_execution_state is not None:
            self.execution.execution_state = self.legacy_execution_state

        # -------------------------------------------------
        # Transitional observability migration
        # -------------------------------------------------
        self.observability.predictive_snapshot = predictive_snapshot_init

        self.observability.global_forecast = global_forecast_init

        self.observability.global_stability = global_stability_init

        self.observability.multi_horizon = multi_horizon_init

        self.observability.stability_stats = stability_stats_init

        self.observability.stability_projection = stability_projection_init

        self.observability.stability_statistics = stability_statistics_init

        self.observability.symbolic_drift = symbolic_drift_init

        self.observability.symbolic_features = symbolic_features_init

        self.observability.system_tension = self.system_tension

        self.observability.ir_state = ir_state_init

        self.observability.cognitive_state = cognitive_state_init

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
    # Observability compatibility layer
    # -----------------------------------------------------

    @property
    def predictive_snapshot(self) -> Any | None:
        return self.observability.predictive_snapshot

    @predictive_snapshot.setter
    def predictive_snapshot(self, value: Any | None) -> None:
        self.observability.predictive_snapshot = value

    @property
    def global_forecast(self) -> Any | None:
        return self.observability.global_forecast

    @global_forecast.setter
    def global_forecast(self, value: Any | None) -> None:
        self.observability.global_forecast = value

    @property
    def global_stability(self) -> Any | None:
        return self.observability.global_stability

    @global_stability.setter
    def global_stability(self, value: Any | None) -> None:
        self.observability.global_stability = value

    @property
    def multi_horizon(self) -> Any | None:
        return self.observability.multi_horizon

    @multi_horizon.setter
    def multi_horizon(self, value: Any | None) -> None:
        self.observability.multi_horizon = value

    @property
    def stability_stats(self) -> Any | None:
        return self.observability.stability_stats

    @stability_stats.setter
    def stability_stats(self, value: Any | None) -> None:
        self.observability.stability_stats = value

    @property
    def stability_projection(self) -> Any | None:
        return self.observability.stability_projection

    @stability_projection.setter
    def stability_projection(self, value: Any | None) -> None:
        self.observability.stability_projection = value

    @property
    def stability_statistics(self) -> Any | None:
        return self.observability.stability_statistics

    @stability_statistics.setter
    def stability_statistics(self, value: Any | None) -> None:
        self.observability.stability_statistics = value

    @property
    def symbolic_drift(self) -> Any | None:
        return self.observability.symbolic_drift

    @symbolic_drift.setter
    def symbolic_drift(self, value: Any | None) -> None:
        self.observability.symbolic_drift = value

    @property
    def symbolic_features(self) -> Any | None:
        return self.observability.symbolic_features

    @symbolic_features.setter
    def symbolic_features(self, value: Any | None) -> None:
        self.observability.symbolic_features = value

    @property
    def ir_state(self) -> CognitiveStateIR | None:
        return self.observability.ir_state

    @ir_state.setter
    def ir_state(self, value: CognitiveStateIR | None) -> None:
        self.observability.ir_state = value

    @property
    def cognitive_state(self) -> Any | None:
        return self.observability.cognitive_state

    @cognitive_state.setter
    def cognitive_state(self, value: Any | None) -> None:
        self.observability.cognitive_state = value

    # -----------------------------------------------------
    # Decision compatibility layer
    # -----------------------------------------------------

    @property
    def decision_result(self) -> Any | None:
        return self.decision_layer.decision_result

    @decision_result.setter
    def decision_result(self, value: Any | None) -> None:
        self.decision_layer.decision_result = value

    @property
    def ir_decision(self) -> CognitiveDecisionIR | None:
        return self.decision_layer.ir_decision

    @ir_decision.setter
    def ir_decision(self, value: CognitiveDecisionIR | None) -> None:
        self.decision_layer.ir_decision = value

    @property
    def bundle(self) -> Any | None:
        return self.decision_layer.bundle

    @bundle.setter
    def bundle(self, value: Any | None) -> None:
        self.decision_layer.bundle = value
