# arvis/conversation/conversation_strategy_dynamics.py

from arvis.conversation.conversation_state import ConversationState
from arvis.conversation.response_strategy_type import ResponseStrategyType


class ConversationStrategyDynamics:
    """
    Applies temporal dynamics to conversational strategy selection.

    Responsibilities:
    - add inertia to avoid unnecessary oscillations
    - preserve legitimate hard transitions (e.g. ABSTENTION)
    - prepare future integration with more advanced stability controls
    """

    # Minimum streak before allowing some strategy switches
    MIN_STREAK_FOR_SWITCH = 2

    @staticmethod
    def apply(
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:
        """
        Apply lightweight temporal dynamics before policy enforcement.

        Rules:
        - first turn: accept proposed strategy
        - if unchanged: keep it
        - ABSTENTION always has priority
        - CONFIRMATION can interrupt immediately
        - ACTION can interrupt immediately
        - informational/social oscillations are damped until streak threshold
        """

        last = state.last_strategy

        if last is None:
            return proposed_strategy

        if proposed_strategy == last:
            return proposed_strategy

        if proposed_strategy == ResponseStrategyType.ABSTENTION:
            return proposed_strategy

        if proposed_strategy == ResponseStrategyType.CONFIRMATION:
            return proposed_strategy

        if proposed_strategy == ResponseStrategyType.ACTION:
            return proposed_strategy

        if state.strategy_streak < ConversationStrategyDynamics.MIN_STREAK_FOR_SWITCH:
            # memory can reduce inertia (user preference adaptation)
            if state.signals.get("memory_pressure", 0) > 0:
                return proposed_strategy
            return last

        return proposed_strategy
