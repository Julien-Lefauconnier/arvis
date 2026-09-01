# arvis/kernel/pipeline/cognitive_pipeline_context.py

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import ConfirmationResult
from arvis.cognition.conflict.conflict_policy_result import ConflictPolicyResult
from arvis.cognition.control.temporal_modulation import TemporalModulation
from arvis.cognition.control.temporal_pressure import TemporalPressureSnapshot
from arvis.cognition.conversation.conversation_context import ConversationContext
from arvis.cognition.conversation.conversation_signal import ConversationSignal
from arvis.cognition.events.base_event import BaseEvent
from arvis.cognition.governance.governance_decision import GovernanceDecision
from arvis.cognition.pending.pending_cognitive_action import PendingCognitiveAction
from arvis.cognition.policy import CognitivePolicyResult
from arvis.ir.context import CognitiveContextIR
from arvis.ir.envelope import CognitiveIREnvelope
from arvis.ir.gate import CognitiveGateIR
from arvis.ir.input import CognitiveInputIR
from arvis.kernel.execution.cognitive_execution_state import CognitiveExecutionState
from arvis.kernel.pipeline.context.decision_context import (
    PipelineDecisionContext,
)
from arvis.kernel.pipeline.context.error_context import (
    PipelineErrorContext,
)
from arvis.kernel.pipeline.context.execution_context import (
    PipelineExecutionContext,
)
from arvis.kernel.pipeline.context.journal_context import (
    PipelineJournalContext,
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
from arvis.kernel_core.access.models import Principal
from arvis.math.signals.conflict import ConflictSignal as ConflictPressureSignal

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline_result import (
        CognitivePipelineResult,
    )


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
    # Trusted ambient identity stamped by the host/runtime composition. It is
    # never derived from request payloads or cognition.
    principal: Principal | None = None

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
    # Journal context (typed storage of cross-component signals;
    # ctx.extra carries the exports, see the extra doctrine below)
    # -------------------------
    journal: PipelineJournalContext = field(
        default_factory=PipelineJournalContext,
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
    # NOTE (campaign OBS, LOT O4):
    # Scientific, observability, execution and tooling state is owned
    # exclusively by the bounded sub-contexts (ctx.scientific.*,
    # ctx.observability.*, ctx.execution.*, ctx.tooling.*,
    # ctx.error_state.*). The historical root-level mirror properties
    # are gone; the facade ratchet pins that they stay gone and that
    # no code resurrects their names as dynamic instance attributes.
    # Duck-tolerant callsites read through the accessor modules
    # (scientific_accessors, observability_accessors,
    # tooling_accessors).
    # -----------------------------------------------------

    # -----------------------------------------
    # Global stability enforcement policy
    # "ignore" | "confirm" | "abstain"
    # -----------------------------------------
    global_stability_action: str = "ignore"
    # A4/B5: switching safety envelope mode. "soft" keeps switching as
    # observability only; any other value feeds the measured switching
    # safety into the validity envelope. Production sets "enforce".
    switching_envelope_mode: str = "soft"
    # F-001-a5: input-risk posture. "graded" allows the pure-scalar
    # grading path of the input-risk gate; any other value (production
    # sets "harden_only", unknown values included) restricts a declared
    # risk to harden-only.
    input_risk_mode: str = "graded"

    # Governance profile that set the postures above ("local",
    # "production"). Recorded into CognitiveContextIR.runtime_mode so a
    # replay reapplies the same postures from the record (D-a), never
    # from the replayer's environment.
    runtime_profile: str = "local"
    # -------------------------
    # Control layer
    # -------------------------
    control_snapshot: Any | None = None
    control: Any | None = None
    change_budget: Any | None = None

    # -------------------------
    # Stage-published working state (declared in campaign STRUCT,
    # LOT S2)
    # -------------------------
    # These fields used to be set dynamically by stages and read
    # downstream through getattr with defaults, invisible to the type
    # checker. Declaring them makes the inter-stage protocol explicit
    # and typo-safe. Several carry Any deliberately: their writers
    # publish heterogeneous shapes today (see the control stage notes);
    # tightening them is part of the ctx.extra / mirror migration
    # (LOT S4).
    conflict: list[ConflictPolicyResult] | None = None
    conflict_pressure: ConflictPressureSignal | None = None
    # Single-writer channel owned by the temporal stage (DS3, LOT S5):
    # the control stage consumes the clamped modulation.
    temporal_pressure: TemporalPressureSnapshot | None = None
    temporal_modulation: TemporalModulation | None = None
    memory_mode: str | None = None
    memory_constraints_active: bool = False
    kappa_band: str | None = None
    adaptive_control: Any | None = None
    slow_divergence: float | None = None
    regime_confidence: float | None = None

    # Gate-published channels (declared in LOT S4; the gate stage
    # previously created them dynamically at initialization).
    stability_certificate: dict[str, Any] = field(
        default_factory=lambda: {
            "local": False,
            "global": True,
            "switching": True,
            "delta_negative": True,
            "exponential": True,
        }
    )
    system_confidence: float = 0.0

    # Private mirror channel: single-writer scalar mirrors consumed by
    # the gate, the projection and the IR adapter. Scheduled for
    # migration into typed sub-contexts (LOT S4); do not add users.
    _dv: float | None = None
    _epsilon: float | None = None
    _effective_epsilon: float | None = None
    _cognitive_mode: Any | None = None

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

    # Lifecycle latches (campaign OBS, LOT O3). Typed storage for the
    # prepare/finalize idempotency guards and the finalized-result
    # cache. The historical ``__pipeline_prepared`` /
    # ``__pipeline_finalized`` / ``__pipeline_result`` extra keys
    # remain as write-only exports for byte-identical host output;
    # arvis reads only these fields, so seeding the extra keys can no
    # longer skip preparation or hijack the cached result.
    _pipeline_prepared: bool = False
    _pipeline_finalized: bool = False
    _pipeline_result: "CognitivePipelineResult | None" = field(
        default=None,
        repr=False,
    )

    # -----------------------------------------------------
    # Legacy compatibility layer
    # -----------------------------------------------------
    # Transitional compatibility input preserved during
    # runtime ownership migration.
    # Tracked in VERSIONING.md, "Transitional surfaces on the way
    # out": removed under the deprecation window once every callsite
    # composes ctx.execution.* directly.
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
    # Extra channel (doctrine, campaign STRUCT LOT S4)
    # -------------------------
    # ``extra`` serves exactly two roles today:
    #
    # 1. HOST BOUNDARY CHANNEL: keys a host passes into run(...) or
    #    reads back from the result. Documented keys: input_data,
    #    session_id, conversation_mode, retrieval_snapshot,
    #    scientific_state (in) / scientific_state_next (out; the
    #    threaded trajectory contract), retry_tool, tool_retry_count,
    #    and the compliance injection channel
    #    (preserve_injected_lyapunov, delta_w, stable).
    #    Host CONTROLS never ride this channel (F-001): postures and
    #    overrides come from composition.
    #
    # 2. RUN OBSERVABILITY JOURNAL: keys the stages export for views,
    #    IR and tests (fusion_reasons, verdict_transition_trace,
    #    final_reason_codes, monitor_snapshot, input_risk, warnings,
    #    llm_observation/evaluation, tool_results, syscall_results,
    #    ...). These are OUTPUT records, written once and never used
    #    to steer a later stage; migrating them into typed
    #    observability contexts is the tracked follow-up of this
    #    campaign.
    #
    # Internal stage-to-stage state does NOT belong here: it goes in
    # declared fields or the typed sub-contexts.
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

    def _ensure_execution_state(
        self,
    ) -> CognitiveExecutionState:
        if self.execution.execution_state is None:
            self.execution.execution_state = CognitiveExecutionState()

        return self.execution.execution_state

    # Legacy projection properties

    # -----------------------------------------------------
    # Decision compatibility layer
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Canonical scientific compatibility properties
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Transitional scientific compatibility properties
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Error compatibility layer
    # -----------------------------------------------------

    # -------------------------
    # Runtime
    # -------------------------


PRODUCTION_PROFILE = "production"


def apply_runtime_postures(
    ctx: "CognitivePipelineContext", runtime_profile: str | None
) -> None:
    """Apply the governing postures derived from the runtime profile.

    Single source of truth used by the fresh-run context builder AND
    the replay context builder: the postures that governed a run are
    part of the record and are reapplied on replay from the recorded
    profile, never from the replayer's environment (decision D-a). The
    permissive defaults are research settings; the production profile
    enforces the global stability axis, feeds switching safety into the
    validity envelope (F-002 / A4), and restricts a caller-declared
    risk to harden-only (F-001-a5).
    """
    ctx.runtime_profile = runtime_profile or "local"
    if ctx.runtime_profile == PRODUCTION_PROFILE:
        ctx.global_stability_action = "confirm"
        ctx.switching_envelope_mode = "enforce"
        ctx.input_risk_mode = "harden_only"
