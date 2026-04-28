# arvis/cognition/coherence/coherence_policy.py


from arvis.cognition.coherence.change_budget import ChangeBudget
from arvis.cognition.policy import (
    CognitivePolicyResult,
    CognitiveSignalSnapshot,
)


class CoherencePolicy:
    """
    Coherence policy detecting excessive change oscillation.

    This policy:
    - never corrects
    - never stabilizes automatically
    - never executes actions
    """

    POLICY_NAME = "coherence_policy"

    def evaluate(
        self,
        snapshot: CognitiveSignalSnapshot,
        budget: ChangeBudget,
    ) -> CognitivePolicyResult | None:
        """
        Evaluate coherence constraints and optionally produce
        a declarative stability warning.

        Returns:
            - CognitivePolicyResult
            - or None (no suggestion)
        """

        if snapshot is None or budget is None:
            return None

        try:
            current = int(budget.current_changes)
            maximum = int(budget.max_changes)
        except Exception:
            return None

        if current > maximum:
            return CognitivePolicyResult(
                policy_name=self.POLICY_NAME,
                dimension="coherence",
                suggestion_type="stability_warning",
                rationale="Change budget exceeded, potential instability detected",
            )

        return None
