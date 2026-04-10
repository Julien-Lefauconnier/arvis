# arvis/conversation/conversation_future_simulator.py

from arvis.conversation.response_strategy_type import (
    ResponseStrategyType,
)


class ConversationFutureSimulator:
    """
    Simulates short conversational futures to detect instability.
    """

    MAX_HORIZON = 2

    @staticmethod
    def simulate(
        *,
        strategy: ResponseStrategyType,
        collapse_risk: float | None,
        uncertainty: float | None,
    ) -> ResponseStrategyType:

        if collapse_risk is None:
            collapse_risk = 0.0

        if uncertainty is None:
            uncertainty = 0.0

        projected_risk = collapse_risk + (uncertainty * 0.3)

        if projected_risk > 0.85:
            return ResponseStrategyType.ABSTENTION

        return strategy