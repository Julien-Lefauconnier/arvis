# arvis/conversation/conversation_predictive_strategy.py

from typing import Any, Protocol

from arvis.conversation.response_strategy_type import ResponseStrategyType


class _StateProtocol(Protocol):
    signals: dict[str, Any]


class ConversationPredictiveStrategy:
    """
    Selects strategy using predictive stability signals.
    """

    @staticmethod
    def choose(
        strategy: ResponseStrategyType,
        state: _StateProtocol,
    ) -> ResponseStrategyType:
        collapse_risk = state.signals.get("world_collapse_risk", 0.0)
        uncertainty = state.signals.get("uncertainty", 0.0)

        if collapse_risk > 0.8:
            return ResponseStrategyType.ABSTENTION

        if uncertainty > 0.7:
            return ResponseStrategyType.CONFIRMATION

        return strategy
