# arvis/cognition/temporal/temporal_policy.py

from typing import Optional

from arvis.cognition.temporal.temporal_context import TemporalContext
from arvis.cognition.policy import (
    CognitiveSignalSnapshot,
    CognitivePolicyResult,
)


class TemporalPolicy:
    """
    Temporal policy producing declarative timing suggestions.

    This policy:
    - never predicts
    - never plans
    - never mutates inputs
    - never executes actions
    """

    POLICY_NAME = "temporal_policy"

    def evaluate(
        self,
        snapshot: CognitiveSignalSnapshot,
        context: TemporalContext,
    ) -> Optional[CognitivePolicyResult]:
        """
        Evaluate temporal constraints and optionally produce
        a declarative policy suggestion.

        Returns:
            - CognitivePolicyResult
            - or None (no suggestion)
        """

        elapsed = context.current_timestamp - context.last_seen_timestamp

        if elapsed < context.cooldown_seconds:
            return CognitivePolicyResult(
                policy_name=self.POLICY_NAME,
                dimension="temporal",
                suggestion_type="cooldown",
                rationale="Cooldown period not yet elapsed",
            )

        return None
