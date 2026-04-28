# arvis/cognition/attention/attention_policy.py


from arvis.cognition.attention.attention_context import AttentionContext
from arvis.cognition.policy import (
    CognitivePolicyResult,
    CognitiveSignalSnapshot,
)


class AttentionPolicy:
    """
    Declarative attention policy.
    """

    POLICY_NAME = "attention_policy"

    def evaluate(
        self,
        snapshot: CognitiveSignalSnapshot,
        context: AttentionContext,
    ) -> CognitivePolicyResult | None:
        if context.current_load > context.max_items:
            return CognitivePolicyResult(
                policy_name=self.POLICY_NAME,
                dimension="attention",
                suggestion_type="limit_exposure",
                rationale="Current attention load exceeds configured maximum",
            )

        return None
