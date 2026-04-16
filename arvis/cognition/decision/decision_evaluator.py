# arvis/cognition/decision/decision_evaluator.py

from typing import Any

from arvis.cognition.decision.decision_signal import DecisionSignal


class DecisionEvaluator:
    """
    Pure decision evaluator.
    """

    def evaluate(self, ctx: Any) -> DecisionSignal:
        """
        Accepts pipeline context directly (kernel-first design).
        """

        cognitive_input = getattr(ctx, "cognitive_input", None)
        intent_type = getattr(cognitive_input, "intent_type", None)

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
            return DecisionSignal(
                reason="action_request",
                memory_influence=memory_influence,
            )

        if intent_type == "search":
            return DecisionSignal(
                reason="search",
                memory_influence=memory_influence,
            )

        if intent_type == "question":
            return DecisionSignal(
                reason="informational_query",
                memory_influence=memory_influence,
            )

        return DecisionSignal(
            reason="unknown",
            memory_influence=memory_influence,
        )