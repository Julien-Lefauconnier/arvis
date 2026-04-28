# arvis/conversation/conversation_trajectory_controller.py

from arvis.conversation.conversation_state import ConversationState
from arvis.conversation.response_strategy_type import ResponseStrategyType


class ConversationTrajectoryController:
    """
    Controls the trajectory of the dialogue over time.
    """

    MAX_STRATEGY_SWITCH_RATE = 0.6

    @staticmethod
    def regulate(
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:
        if state.turn_count < 2:
            return proposed_strategy

        switch_rate = 1 - (state.strategy_streak / state.turn_count)

        if switch_rate > ConversationTrajectoryController.MAX_STRATEGY_SWITCH_RATE:
            return state.last_strategy or proposed_strategy

        return proposed_strategy
