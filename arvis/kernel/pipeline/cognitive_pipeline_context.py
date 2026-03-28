# arvis/kernel/pipeline/cognitive_pipeline_context.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.slow_state import SlowState
from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import ConfirmationResult
from arvis.cognition.conversation.conversation_context import ConversationContext
from arvis.cognition.conversation.conversation_signal import ConversationSignal
from arvis.cognition.governance.governance_decision import GovernanceDecision
from arvis.cognition.pending.pending_cognitive_action import PendingCognitiveAction
from arvis.cognition.events.base_event import BaseEvent
from arvis.cognition.policy import CognitivePolicyResult
from arvis.action.action_decision import ActionDecision
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.kernel.trace.decision_trace import DecisionTrace
from arvis.math.switching.switching_runtime import SwitchingRuntime
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.stability.validity_envelope import ValidityEnvelope
from arvis.ir.input import CognitiveInputIR
from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.state import CognitiveStateIR
from arvis.ir.gate import CognitiveGateIR
from arvis.kernel.projection.certificate import ProjectionCertificate
from arvis.kernel.pipeline.gate_overrides import GateOverrides

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
    ir_input: Optional[CognitiveInputIR] = None
    ir_context: Optional[CognitiveContextIR] = None
    long_memory: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Any] = field(default_factory=list)
    introspection: Optional[Any] = None
    explanation: Optional[Any] = None
    previous_bundle: Optional[Any] = None
    previous_budget: Optional[Any] = None

    # -------------------------
    # Decision layer
    # -------------------------
    decision_result: Optional[Any] = None
    decision: Optional[Any] = None
    ir_decision: Optional[CognitiveDecisionIR] = None

    # -------------------------
    # Bundle layer
    # -------------------------
    bundle: Optional[Any] = None

    # -------------------------
    # Scientific / core layer
    # -------------------------
    scientific_snapshot: Optional[Any] = None
    collapse_risk: RiskSignal | float = 0.0
    uncertainty: UncertaintySignal | float | None = None
    # Fast Lyapunov state (x)
    prev_lyap: Optional[LyapunovState] = None
    cur_lyap: Optional[LyapunovState] = None
    prev_quadratic_lyap_state: Optional[Any] = None
    cur_quadratic_lyap_state: Optional[Any] = None
    quadratic_lyap_snapshot: Optional[Any] = None
    quadratic_comparability: Optional[Any] = None
    # Slow state (z)
    slow_state: Optional[SlowState] = None
    slow_state_prev: Optional[SlowState] = None
    # Symbolic state (used for T(x))
    symbolic_state: Optional[SymbolicState] = None
    symbolic_state_prev: Optional[SymbolicState] = None
    # Composite Lyapunov tracking
    w_current: Optional[float] = None
    w_prev: Optional[float] = None
    delta_w: Optional[float] = None

    drift_score: DriftSignal | float = 0.0
    regime: Optional[str] = None
    stable: Optional[bool] = None
    regime_confidence: float = 0.0
    theoretical_regime: Optional[Any] = None
    fast_dynamics: Optional[Any] = None
    perturbation: Optional[Any] = None

    # -------------------------
    # Switching runtime (theorem)
    # -------------------------
    switching_runtime: Optional[SwitchingRuntime] = None
    switching_params: Optional[Any] = None
    switching_safe: Optional[bool] = None
    switching_metrics: Dict[str, Any] = field(default_factory=dict)
    # -------------------------
    # Adaptive stability (canonical)
    # -------------------------
    adaptive_snapshot: Optional[AdaptiveSnapshot] = None
    validity_envelope: Optional[ValidityEnvelope] = None

    use_paper_slow_dynamics: bool = False
    use_paper_composite_gate: bool = False
    global_stability_metrics: Optional[Any] = None
    enforce_global_stability: bool = False
    # -----------------------------------------
    # Global stability enforcement policy
    # "ignore" | "confirm" | "abstain"
    # -----------------------------------------
    global_stability_action: str = "ignore"
    # -------------------------
    # Control layer
    # -------------------------
    control_snapshot: Optional[Any] = None
    control: Optional[Any] = None
    change_budget: Optional[Any] = None

    # -------------------------
    # Gate layer
    # -------------------------
    gate_result: Optional[Any] = None
    ir_gate: Optional[CognitiveGateIR] = None

    # -------------------------
    # Confirmation layer
    # -------------------------
    confirmation_request: ConfirmationRequest | None = None
    confirmation_result: ConfirmationResult | None = None
    
    # -------------------------
    # Execution layer
    # -------------------------
    executable_intent: Optional[Any] = None
    action_decision: Optional[ActionDecision] = None
    execution_status: Optional[ExecutionGateStatus] = None
    can_execute: bool = False
    requires_confirmation: bool = False

    # Internal stage flags
    _can_execute: bool = False
    _requires_confirmation: bool = False
    _needs_confirmation: bool = False

    # -------------------------
    # Extensions
    # -------------------------
    extra: Dict[str, Any] = field(default_factory=dict)

    # -------------------------
    # Observability (read-only projections)
    # -------------------------
    predictive_snapshot: Optional[Any] = None
    global_forecast: Optional[Any] = None
    global_stability: Optional[Any] = None
    multi_horizon: Optional[Any] = None
    stability_stats: Optional[Any] = None
    stability_projection: Optional[Any] = None
    stability_statistics: Optional[Any] = None
    symbolic_drift: Optional[Any] = None
    symbolic_features: Optional[Any] = None
    system_tension: Optional[Any] = None
    ir_state: Optional[CognitiveStateIR] = None

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
    trace: Optional[DecisionTrace] = None

    # -------------------------
    # Projection (Pi certification)
    # -------------------------
    projection_certificate: Optional[ProjectionCertificate] = None
    projection_domain_valid: Optional[bool] = None
    projection_margin: Optional[float] = None

    # -------------------------
    # Gate overrides
    # -------------------------
    gate_overrides: Optional[GateOverrides] = None
    