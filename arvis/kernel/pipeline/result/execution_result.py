# arvis/kernel/pipeline/result/execution_result.py

from dataclasses import dataclass
from typing import Any

from arvis.action.action_decision import ActionDecision
from arvis.cognition.confirmation.confirmation_request import (
    ConfirmationRequest,
)
from arvis.kernel.execution.execution_gate_status import (
    ExecutionGateStatus,
)


@dataclass(frozen=True)
class PipelineExecutionResult:
    execution_status: ExecutionGateStatus
    can_execute: bool
    requires_confirmation: bool

    executable_intent: Any | None = None
    action_decision: ActionDecision | None = None
    confirmation_request: ConfirmationRequest | None = None
