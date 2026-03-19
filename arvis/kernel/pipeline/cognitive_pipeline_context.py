# arvis/kernel/pipeline/cognitive_pipeline_context.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal
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
    long_memory: Dict[str, Any] = field(default_factory=dict)

    # Optional precomputed / external kernel-safe inputs
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
    prev_lyap: Optional[Any] = None
    cur_lyap: Optional[Any] = None
    drift_score: DriftSignal | float = 0.0
    regime: Optional[str] = None
    stable: Optional[bool] = None

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


    symbolic_state: Optional[Any] = None
    symbolic_drift: Optional[Any] = None
    symbolic_features: Optional[Any] = None
    system_tension: Optional[Any] = None

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
    