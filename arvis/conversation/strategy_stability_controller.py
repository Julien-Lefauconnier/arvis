# arvis/conversation/strategy_stability_controller.py

from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.conversation_policy_base import ConversationPolicy

from arvis.conversation.conversation_state import (
    ConversationState,
)


class StrategyStabilityController(ConversationPolicy):
    """
    Apply response strategy transitions.

    Prevents unstable oscillations between strategies
    by introducing conversational inertia.
    """

    MIN_STREAK_FOR_SWITCH = 2

    @staticmethod
    def apply(
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:

        # No previous state → accept proposal
        if state.last_strategy is None:
            return proposed_strategy

        # Same strategy → always allowed
        if proposed_strategy == state.last_strategy:
            return proposed_strategy

        # Prevent rapid oscillation
        if state.strategy_streak < StrategyStabilityController.MIN_STREAK_FOR_SWITCH:
            return state.last_strategy

        return proposed_strategy