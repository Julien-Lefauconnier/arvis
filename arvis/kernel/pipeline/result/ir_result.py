# arvis/kernel/pipeline/result/ir_result.py

from dataclasses import dataclass
from typing import Any

from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.envelope import CognitiveIREnvelope
from arvis.ir.gate import CognitiveGateIR
from arvis.ir.input import CognitiveInputIR
from arvis.ir.state import CognitiveStateIR


@dataclass(frozen=True)
class PipelineIRResult:
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
