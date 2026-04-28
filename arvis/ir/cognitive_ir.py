# arvis/ir/cognitive_ir.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

from arvis.ir.input import CognitiveInputIR
from arvis.ir.context import CognitiveContextIR
from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.state import CognitiveStateIR
from arvis.ir.gate import CognitiveGateIR


@dataclass(frozen=True)
class CognitiveIR:
    """
    Canonical IR aggregation (ZKCS compliant)

    This is the single exportable representation of cognition.
    """

    input: Optional[CognitiveInputIR]
    context: Optional[CognitiveContextIR]
    decision: Optional[CognitiveDecisionIR]
    state: Optional[CognitiveStateIR]
    gate: Optional[CognitiveGateIR]

    projection: Optional[object] = None
    validity: Optional[object] = None
    stability: Optional[object] = None
    adaptive: Optional[object] = None

    # -----------------------------------------
    # TOOL EXECUTION
    # -----------------------------------------
    tools: Optional[List[Dict[str, Any]]] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CognitiveIR":
        from arvis.ir.serialization.cognitive_ir_serializer import CognitiveIRSerializer

        return cast(CognitiveIR, CognitiveIRSerializer.from_dict(data))
