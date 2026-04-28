# arvis/kernel/pipeline/cognitive_pipeline_context.py

from dataclasses import dataclass, field
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
from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.projection.certificate import ProjectionCertificate
from arvis.kernel.trace.decision_trace import DecisionTrace
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.signals import DriftSignal, RiskSignal, UncertaintySignal
from arvis.math.stability.validity_envelope import ValidityEnvelope
from arvis.math.switching.switching_runtime import SwitchingRuntime


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
    # Decision layer
    # -------------------------
    decision_result: Any | None = None
    decision: Any | None = None
    ir_decision: CognitiveDecisionIR | None = None

    # -------------------------
    # Bundle layer
    # -------------------------
    bundle: Any | None = None

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
    executable_intent: Any | None = None
    action_decision: ActionDecision | None = None
    execution_status: ExecutionGateStatus | None = None
    can_execute: bool = False
    requires_confirmation: bool = False

    # Internal stage flags
    _can_execute: bool = False
    _requires_confirmation: bool = False
    _needs_confirmation: bool = False

    # -------------------------
    # Extensions
    # -------------------------
    extra: dict[str, Any] = field(default_factory=dict)

    # -------------------------
    # Observability (read-only projections)
    # -------------------------
    predictive_snapshot: Any | None = None
    global_forecast: Any | None = None
    global_stability: Any | None = None
    multi_horizon: Any | None = None
    stability_stats: Any | None = None
    stability_projection: Any | None = None
    stability_statistics: Any | None = None
    symbolic_drift: Any | None = None
    symbolic_features: Any | None = None
    system_tension: Any | None = None
    ir_state: CognitiveStateIR | None = None
    cognitive_state: Any | None = None

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
    projection_certificate: ProjectionCertificate | None = None
    projection_domain_valid: bool | None = None
    projection_margin: float | None = None
    projected_state: Any | None = None
    pi_state: Any | None = None
    projection_view: dict[str, float] | None = None
    projection_view_raw: dict[str, float] | None = None

    # -------------------------
    # Gate overrides
    # -------------------------
    gate_overrides: GateOverrides | None = None

    # -------------------------
    # Runtime
    # -------------------------
    control_runtime: Any | None = None
