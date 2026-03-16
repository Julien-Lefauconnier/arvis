# arvis/reasoning/gap_to_intent_mapper.py
from typing import List

from arvis.reasoning.reasoning_gap import ReasoningGap, GapType
from arvis.reasoning.reasoning_intent import ReasoningIntent, ReasoningIntentType


class GapToIntentMapper:
    """
    Declarative mapper converting a ReasoningGap
    into one or more ReasoningIntents.

    Kernel guarantees:
    - no execution
    - no side effects
    """

    @staticmethod
    def map(gap: ReasoningGap) -> List[ReasoningIntent]:

        if gap.gap_type == GapType.MISSING_CONTEXT:
            return [
                ReasoningIntent(
                    intent_type=ReasoningIntentType.REQUEST_USER_CLARIFICATION,
                    reason=gap.description,
                    source_ref=gap.origin_ref,
                )
            ]

        return []