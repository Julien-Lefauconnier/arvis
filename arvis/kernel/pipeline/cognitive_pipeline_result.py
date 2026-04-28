# arvis/kernel/pipeline/cognitive_pipeline_result.py

from dataclasses import dataclass
from typing import Any

from arvis.action.action_decision import ActionDecision
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.envelope import CognitiveIREnvelope
from arvis.ir.gate import CognitiveGateIR
from arvis.ir.input import CognitiveInputIR
from arvis.ir.state import CognitiveStateIR
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.kernel.trace.decision_trace import DecisionTrace


@dataclass(frozen=True)
class CognitivePipelineResult:
    """
    Final kernel output.

    No execution.
    No LLM.
    No side effects.
    """

    bundle: Any | None
    decision: Any | None
    scientific: Any | None
    control: Any | None
    gate_result: Any | None
    execution_status: ExecutionGateStatus
    can_execute: bool
    requires_confirmation: bool
    executable_intent: Any | None = None
    action_decision: ActionDecision | None = None
    confirmation_request: ConfirmationRequest | None = None
    trace: DecisionTrace | None = None
    ir_input: CognitiveInputIR | None = None
    ir_context: CognitiveContextIR | None = None
    ir_decision: CognitiveDecisionIR | None = None
    ir_state: CognitiveStateIR | None = None
    ir_gate: CognitiveGateIR | None = None
    ir_projection: Any | None = None
    ir_validity: Any | None = None
    ir_stability: Any | None = None
    ir_adaptive: Any | None = None
    cognitive_ir: Any | None = None
    ir_serialized: dict[str, Any] | None = None
    ir_hash: str | None = None
    ir_envelope: CognitiveIREnvelope | None = None
    cognitive_state: CognitiveState | None = None
