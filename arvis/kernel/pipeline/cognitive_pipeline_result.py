# arvis/kernel/pipeline/cognitive_pipeline_result.py

from dataclasses import dataclass
from typing import Any, Optional

from arvis.action.action_decision import ActionDecision
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.kernel.trace.decision_trace import DecisionTrace
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus


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
    
