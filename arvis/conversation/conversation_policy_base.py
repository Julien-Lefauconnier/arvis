# arvis/conversation/conversation_policy_base.py

from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.conversation_state import ConversationState


class ConversationPolicy:
    """
    Base interface for all conversation policies.
    """

    def apply(
        self,
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:
        raise NotImplementedError
