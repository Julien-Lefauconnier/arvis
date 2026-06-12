# arvis/cognition/decision/decision_evaluator.py

from typing import Any

from arvis.cognition.decision.decision_signal import DecisionSignal
from arvis.uncertainty.uncertainty_inference import UncertaintyInference


class DecisionEvaluator:
    """
    Pure decision evaluator.
    """

    def __init__(self, uncertainty: UncertaintyInference | None = None) -> None:
        self._uncertainty = uncertainty or UncertaintyInference()

    def evaluate(self, ctx: Any) -> DecisionSignal:
        """
        Accepts pipeline context directly (kernel-first design).
        """

        cognitive_input = getattr(ctx, "cognitive_input", None)
        intent_type = getattr(cognitive_input, "intent_type", None)
        if intent_type is None and isinstance(cognitive_input, dict):
            intent_type = cognitive_input.get("intent_type")

        # -----------------------------------------------------
        # Memory influence (ZK-safe projection)
        # -----------------------------------------------------
        memory = getattr(ctx, "memory_projection", None) or {}

        memory_influence = {
            "memory_present": bool(memory),
            "memory_pressure": float(memory.get("memory_pressure", 0.0) or 0.0),
            "memory_has_constraints": bool(memory.get("has_constraints", False)),
        }

        if intent_type == "action":
            reason = "action_request"
        elif intent_type == "search":
            reason = "search"
        elif intent_type == "question":
            reason = "informational_query"
        else:
            reason = "unknown"

        # Decision-layer uncertainty (decision B): perception passes a
        # ZK-safe referential-ambiguity scalar; we turn it into
        # declarative gaps/frames. Absent => 0.0 => no frame.
        if isinstance(cognitive_input, dict):
            raw_ra = cognitive_input.get("referential_ambiguity", 0.0)
            raw_cd = cognitive_input.get("context_dependent", 0.0)
        else:
            raw_ra = getattr(cognitive_input, "referential_ambiguity", 0.0)
            raw_cd = getattr(cognitive_input, "context_dependent", 0.0)
        referential = float(raw_ra or 0.0)
        contextual = float(raw_cd or 0.0)
        inferred = self._uncertainty.infer(
            referential_ambiguity=referential,
            context_dependent=contextual,
            memory_present=bool(memory_influence["memory_present"]),
            reason=reason,
        )

        return DecisionSignal(
            reason=reason,
            memory_influence=memory_influence,
            gaps=inferred.gaps,
            uncertainty_frames=inferred.frames,
            conflicts=inferred.conflicts,
        )
