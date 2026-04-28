# arvis/cognition/suggestion/suggestion_evaluator.py

from typing import List

from arvis.cognition.decision.decision_signal import DecisionSignal
from arvis.cognition.suggestion.suggestion_signal import SuggestionSignal
from arvis.reasoning.reasoning_gap import GapType
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.reasoning.reasoning_intent import ReasoningIntentType


class SuggestionEvaluator:
    def evaluate(self, decision: DecisionSignal) -> List[SuggestionSignal]:
        suggestions = []

        # Gaps
        for gap in decision.gaps:
            if gap.gap_type == GapType.MISSING_CONTEXT:
                suggestions.append(SuggestionSignal("provide_context", "gap"))

            elif gap.gap_type == GapType.AMBIGUOUS_INTENT:
                suggestions.append(SuggestionSignal("request_confirmation", "gap"))

        # Uncertainty
        for frame in decision.uncertainty_frames:
            axes: set[UncertaintyAxis] = getattr(frame, "axes", set())

            if UncertaintyAxis.IRREVERSIBLE_RISK in axes:
                suggestions.append(
                    SuggestionSignal("request_confirmation", "uncertainty")
                )

        # Reasoning intents
        for intent in decision.reasoning_intents:
            if intent.intent_type == ReasoningIntentType.DEFER_ACTION:
                suggestions.append(SuggestionSignal("slow_down_reasoning", "reasoning"))

        return list({s.suggestion_type: s for s in suggestions}.values())
