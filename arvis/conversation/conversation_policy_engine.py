# arvis/conversation/conversation_policy_engine.py

from typing import Protocol

from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.conversation_state import ConversationState
from arvis.conversation.strategy_stability_controller import StrategyStabilityController
from arvis.conversation.conversation_memory_policy import ConversationMemoryPolicy
from arvis.conversation.conversation_adaptive_policy import AdaptiveThresholdPolicy


class _PolicyProtocol(Protocol):
    def apply(
        self,
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:
        ...

class ConversationPolicyEngine:
    """
    Applies conversational policies to stabilize
    and adapt response strategies.

    This component is the future integration point for:
    - user preferences
    - cognitive regime estimation
    - drift detection
    - mathematical stability control
    """

    # --------------------------------------------------
    # POLICY PIPELINE (ORDER MATTERS)
    # --------------------------------------------------
    POLICIES: list[_PolicyProtocol] = [
        StrategyStabilityController(),
        ConversationMemoryPolicy(),
        AdaptiveThresholdPolicy(),
    ]

    @staticmethod
    def _apply_pipeline(
        strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:
        for policy in ConversationPolicyEngine.POLICIES:
            strategy = policy.apply(proposed_strategy=strategy, state=state)
        return strategy

    @staticmethod
    def apply_policy(
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:
        
        return ConversationPolicyEngine._apply_pipeline(
            strategy=proposed_strategy,
            state=state,
        )