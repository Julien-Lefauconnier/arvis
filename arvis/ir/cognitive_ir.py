# arvis/ir/cognitive_ir.py

from dataclasses import dataclass
from typing import Any, cast

from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.gate import CognitiveGateIR
from arvis.ir.input import CognitiveInputIR
from arvis.ir.state import CognitiveStateIR


@dataclass(frozen=True)
class CognitiveIR:
    """
    Canonical IR aggregation (ZKCS compliant)

    This is the single exportable representation of cognition.
    """

    input: CognitiveInputIR | None
    context: CognitiveContextIR | None
    decision: CognitiveDecisionIR | None
    state: CognitiveStateIR | None
    gate: CognitiveGateIR | None

    projection: object | None = None
    validity: object | None = None
    stability: object | None = None
    adaptive: object | None = None

    # -----------------------------------------
    # TOOL EXECUTION
    # -----------------------------------------
    tools: list[dict[str, Any]] | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "CognitiveIR":
        from arvis.ir.serialization.cognitive_ir_serializer import CognitiveIRSerializer

        return cast(CognitiveIR, CognitiveIRSerializer.from_dict(data))
