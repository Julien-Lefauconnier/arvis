# arvis/cognition/decision/decision_evaluator.py

from arvis.cognition.decision.decision_signal import DecisionSignal


class DecisionEvaluator:
    """
    Pure decision evaluator.
    """

    def evaluate(self, ctx) -> DecisionSignal:
        """
        Accepts pipeline context directly (kernel-first design).
        """

        cognitive_input = getattr(ctx, "cognitive_input", None)
        intent_type = getattr(cognitive_input, "intent_type", None)

        if intent_type == "action":
            return DecisionSignal(reason="action_request")

        if intent_type == "search":
            return DecisionSignal(reason="search")

        if intent_type == "question":
            return DecisionSignal(reason="informational_query")

        return DecisionSignal(reason="unknown")