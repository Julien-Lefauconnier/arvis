# arvis/uncertainty/uncertainty_to_intent_mapper.py

from typing import List

from arvis.uncertainty.uncertainty_frame import UncertaintyFrame
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.reasoning.reasoning_intent import (
    ReasoningIntent,
    ReasoningIntentType,
)


class UncertaintyToIntentMapper:
    """
    Declarative mapper converting uncertainty frames
    into reasoning intents.

    - No execution
    - No policy enforcement
    - No decision
    """

    @staticmethod
    def map(frame: UncertaintyFrame) -> List[ReasoningIntent]:
        intents: List[ReasoningIntent] = []

        axes = frame.axes

        # High-impact or irreversible contexts → user clarification recommended
        if (
            UncertaintyAxis.HIGH_IMPACT in axes
            or UncertaintyAxis.IRREVERSIBLE_RISK in axes
        ):
            intents.append(
                ReasoningIntent(
                    intent_type=ReasoningIntentType.REQUEST_USER_CLARIFICATION,
                    reason=(
                        f"High-impact uncertainty detected "
                        f"({frame.label}). User clarification is recommended."
                    ),
                    source_ref=frame.frame_id,
                )
            )

        # Personal or context-dependent → allow weak assumption (explicit)
        elif (
            UncertaintyAxis.USER_SENSITIVE in axes
            or UncertaintyAxis.CONTEXT_DEPENDENT in axes
        ):
            intents.append(
                ReasoningIntent(
                    intent_type=ReasoningIntentType.ALLOW_WEAK_ASSUMPTION,
                    reason=(
                        f"Context-dependent uncertainty detected "
                        f"({frame.label}). Proceeding may require assumptions."
                    ),
                    source_ref=frame.frame_id,
                )
            )

        return intents

# -----------------------------
# Public functional API
# -----------------------------

def map_uncertainty_to_intent(frame: UncertaintyFrame) -> List[ReasoningIntent]:
    return UncertaintyToIntentMapper.map(frame)