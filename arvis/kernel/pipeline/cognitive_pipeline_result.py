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
from arvis.kernel.pipeline.result.execution_result import (
    PipelineExecutionResult,
)
from arvis.kernel.pipeline.result.ir_result import (
    PipelineIRResult,
)
from arvis.kernel.pipeline.result.observability_result import (
    PipelineObservabilityResult,
)
from arvis.kernel.trace.decision_trace import DecisionTrace


@dataclass(frozen=True)
class CognitivePipelineResult:
    """
    Final immutable kernel output.

    This object acts simultaneously as:

    1. Stable root-level kernel result envelope
    2. Projection-oriented domain access surface
    3. Transitional compatibility layer

    Structured projections:
    - execution
    - ir
    - observability

    Compatibility properties expose the former flat API
    during the progressive migration toward nested access.

    Design constraints:
    - immutable
    - replay-safe
    - serialization-safe
    - side-effect free
    - LLM-independent
    """

    # -----------------------------------------------------
    # Structured result projections
    # -----------------------------------------------------

    execution: PipelineExecutionResult
    ir: PipelineIRResult
    observability: PipelineObservabilityResult

    # -----------------------------------------------------
    # Core root-level metadata
    # -----------------------------------------------------

    bundle: Any | None
    decision: Any | None
    gate_result: Any | None
    trace: DecisionTrace | None = None

    # -----------------------------------------------------
    # Transitional compatibility properties
    # TODO(arvis-result-v2):
    # remove after full migration to nested result model
    # -----------------------------------------------------

    @property
    def scientific(self) -> Any | None:
        return self.observability.scientific

    @property
    def control(self) -> Any | None:
        return self.observability.control

    @property
    def execution_status(self) -> ExecutionGateStatus:
        return self.execution.execution_status

    @property
    def can_execute(self) -> bool:
        return self.execution.can_execute

    @property
    def requires_confirmation(self) -> bool:
        return self.execution.requires_confirmation

    @property
    def executable_intent(self) -> Any | None:
        return self.execution.executable_intent

    @property
    def action_decision(self) -> ActionDecision | None:
        return self.execution.action_decision

    @property
    def confirmation_request(self) -> ConfirmationRequest | None:
        return self.execution.confirmation_request

    @property
    def ir_input(self) -> CognitiveInputIR | None:
        return self.ir.ir_input

    @property
    def ir_context(self) -> CognitiveContextIR | None:
        return self.ir.ir_context

    @property
    def ir_decision(self) -> CognitiveDecisionIR | None:
        return self.ir.ir_decision

    @property
    def ir_state(self) -> CognitiveStateIR | None:
        return self.ir.ir_state

    @property
    def ir_gate(self) -> CognitiveGateIR | None:
        return self.ir.ir_gate

    @property
    def ir_projection(self) -> Any | None:
        return self.ir.ir_projection

    @property
    def ir_validity(self) -> Any | None:
        return self.ir.ir_validity

    @property
    def ir_stability(self) -> Any | None:
        return self.ir.ir_stability

    @property
    def ir_adaptive(self) -> Any | None:
        return self.ir.ir_adaptive

    @property
    def cognitive_ir(self) -> Any | None:
        return self.ir.cognitive_ir

    @property
    def ir_serialized(self) -> dict[str, Any] | None:
        return self.ir.ir_serialized

    @property
    def ir_hash(self) -> str | None:
        return self.ir.ir_hash

    @property
    def ir_envelope(self) -> CognitiveIREnvelope | None:
        return self.ir.ir_envelope

    @property
    def cognitive_state(self) -> CognitiveState | None:
        return getattr(self.observability, "cognitive_state", None)
