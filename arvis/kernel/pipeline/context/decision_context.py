# arvis/kernel/pipeline/context/decision_context.py

from dataclasses import dataclass

from arvis.cognition.bundle.cognitive_bundle_snapshot import (
    CognitiveBundleSnapshot,
)
from arvis.cognition.decision.decision_result import DecisionResult
from arvis.ir.decision import CognitiveDecisionIR


@dataclass
class PipelineDecisionContext:
    """
    Structured decision-layer pipeline state.

    Transitional extraction from CognitivePipelineContext.

    Responsibilities:
    - canonical decision output
    - bundle linkage
    - IR decision projection
    """

    decision_result: DecisionResult | None = None
    ir_decision: CognitiveDecisionIR | None = None
    bundle: CognitiveBundleSnapshot | None = None

    @property
    def bundle_id(self) -> str:
        if self.bundle is None:
            return "bundle"

        return str(getattr(self.bundle, "bundle_id", "bundle"))
