# arvis/kernel/pipeline/cognitive_pipeline_result.py

from dataclasses import dataclass
from typing import Any, Optional

from arvis.action.action_decision import ActionDecision
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.kernel.trace.decision_trace import DecisionTrace
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.ir.input import CognitiveInputIR
from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.state import CognitiveStateIR
from arvis.ir.gate import CognitiveGateIR


@dataclass(frozen=True)
class CognitivePipelineResult:
    """
    Final kernel output.

    No execution.
    No LLM.
    No side effects.
    """

    bundle: Optional[Any]
    decision: Optional[Any]
    scientific: Optional[Any]
    control: Optional[Any]
    gate_result: Optional[Any]
    execution_status: ExecutionGateStatus
    can_execute: bool
    requires_confirmation: bool
    executable_intent: Optional[Any] = None
    action_decision: Optional[ActionDecision] = None
    confirmation_request: ConfirmationRequest | None = None
    trace: Optional[DecisionTrace] = None
    ir_input: Optional[CognitiveInputIR] = None
    ir_context: Optional[CognitiveContextIR] = None
    ir_decision: Optional[CognitiveDecisionIR] = None
    ir_state: Optional[CognitiveStateIR] = None
    ir_gate: Optional[CognitiveGateIR] = None
    
