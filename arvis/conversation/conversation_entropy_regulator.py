# arvis/conversation/conversation_entropy_regulator.py

from arvis.conversation.conversation_state import ConversationState
from arvis.conversation.response_strategy_type import (
    ResponseStrategyType,
)

import math


class ConversationEntropyRegulator:
    """
    Controls conversational entropy using strategy weight distribution.
    """

    MIN_ENTROPY = 0.15
    MAX_ENTROPY = 1.2

    @staticmethod
    def compute_entropy(state: ConversationState) -> float:

        weights = getattr(state, "strategy_weights", None)

        if not weights:
            return 0.0

        entropy = 0.0

        for p in weights.values():

            if p > 0:
                entropy -= p * math.log(p)

        return entropy

    @staticmethod
    def regulate(
        *,
        strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:

        entropy = ConversationEntropyRegulator.compute_entropy(state)

        state.signals["entropy"] = entropy

        if entropy < ConversationEntropyRegulator.MIN_ENTROPY:
            return ResponseStrategyType.CONFIRMATION

        if entropy > ConversationEntropyRegulator.MAX_ENTROPY:
            return state.last_strategy or strategy

        return strategy