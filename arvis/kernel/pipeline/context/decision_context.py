# arvis/kernel/pipeline/context/decision_context.py

from dataclasses import dataclass
from typing import Any

from arvis.ir.decision import CognitiveDecisionIR


@dataclass
class PipelineDecisionContext:
    """
    Structured decision-layer pipeline state.

    Transitional extraction from CognitivePipelineContext.

    Responsibilities:
    - decision outputs
    - bundle linkage
    - IR decision projection
    """

    decision_result: Any | None = None
    decision: Any | None = None
    ir_decision: CognitiveDecisionIR | None = None
    bundle: Any | None = None
