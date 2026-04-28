# arvis/conversation/conversation_attractor_model.py

from typing import Any, Protocol

from arvis.conversation.response_strategy_type import (
    ResponseStrategyType,
)


class _StateProtocol(Protocol):
    signals: dict[str, Any]


class ConversationAttractorModel:
    """
    Conversational attractor field.
    Pulls strategies toward stable dialogue states.
    """

    @staticmethod
    def attract(
        *,
        strategy: ResponseStrategyType,
        uncertainty: float | None,
        coherence: float | None,
        state: _StateProtocol | None = None,
    ) -> ResponseStrategyType:
        # --------------------------------------------
        # MEMORY SIGNALS
        # --------------------------------------------
        memory_pressure = 0
        has_constraints = False

        if state is not None:
            signals = state.signals or {}
            memory_pressure = signals.get("memory_pressure", 0)
            has_constraints = signals.get("has_constraints", False)

        if uncertainty is not None and uncertainty > 0.7:
            return ResponseStrategyType.CONFIRMATION

        if coherence is not None and coherence < 0.3:
            return ResponseStrategyType.CONFIRMATION

        # --------------------------------------------
        # MEMORY-DRIVEN ATTRACTOR SHIFT
        # --------------------------------------------

        # Strong constraint → stable attractor = confirmation
        if has_constraints:
            if strategy == ResponseStrategyType.ACTION:
                return ResponseStrategyType.CONFIRMATION

        # High memory load → avoid aggressive attractors
        if memory_pressure >= 5:
            if strategy == ResponseStrategyType.ACTION:
                return ResponseStrategyType.CONFIRMATION

        elif memory_pressure >= 3:
            if strategy == ResponseStrategyType.ACTION:
                return ResponseStrategyType.CONFIRMATION

        return strategy
