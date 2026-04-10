# arvis/conversation/conversation_adaptive_policy.py

from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.conversation_state import ConversationState
from arvis.conversation.conversation_policy_base import ConversationPolicy


class AdaptiveThresholdPolicy(ConversationPolicy):
    """
    Adjusts behavior based on instability and memory signals.

    This is a SOFT policy layer:
    - does NOT override hard safety decisions
    - biases strategies toward more conservative behavior
    """

    def apply(
        self,
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:

        signals = state.signals or {}

        instability = signals.get("instability", 0.0)
        memory_instability = signals.get("memory_instability", 0.0)
        delta_w = signals.get("delta_w", 0.0)

        # --------------------------------------------
        # GLOBAL PRESSURE
        # --------------------------------------------
        memory_structural = signals.get("memory_structural", 0.0)

        pressure = (
            0.3 * instability +
            0.25 * memory_instability +
            0.3 * memory_structural +
            0.15 * max(delta_w, 0.0)
        )

        # --------------------------------------------
        # NON-LINEAR MEMORY AMPLIFICATION
        # --------------------------------------------
        # memory becomes dominant when high (structural persistence)
        pressure += 0.25 * (memory_instability ** 2)
        pressure += 0.15 * (memory_structural ** 2)

        pressure = min(max(pressure, 0.0), 1.0)

        # --------------------------------------------
        # BEHAVIORAL BIAS
        # --------------------------------------------
        # progressively push toward conservative strategies

        if pressure > 0.6:
            return ResponseStrategyType.ABSTENTION

        if pressure > 0.3:
            return ResponseStrategyType.CONFIRMATION

        return proposed_strategy