# arvis/cognition/coherence/coherence_policy.py

from typing import Optional

from arvis.cognition.coherence.change_budget import ChangeBudget
from arvis.cognition.policy import (
    CognitiveSignalSnapshot,
    CognitivePolicyResult,
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
    ) -> Optional[CognitivePolicyResult]:
        """
        Evaluate coherence constraints and optionally produce
        a declarative stability warning.

        Returns:
            - CognitivePolicyResult
            - or None (no suggestion)
        """

        if budget.current_changes > budget.max_changes:
            return CognitivePolicyResult(
                policy_name=self.POLICY_NAME,
                dimension="coherence",
                suggestion_type="stability_warning",
                rationale="Change budget exceeded, potential instability detected",
            )

        return None
