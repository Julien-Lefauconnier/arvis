# arvis/conversation/conversation_memory_policy.py

from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.conversation_state import ConversationState


class ConversationMemoryPolicy:
    """
    Applies memory-derived conversational constraints.

    Design goals:
    - scalable: one place for all memory-based strategy constraints
    - ZKCS-safe: only uses projected declarative signals
    - non-invasive: does not mutate memory, only interprets safe flags
    """

    @staticmethod
    def apply(
        *,
        proposed_strategy: ResponseStrategyType,
        state: ConversationState,
    ) -> ResponseStrategyType:
        signals = state.signals or {}

        constraints = signals.get("constraints") or []
        has_constraints = bool(signals.get("has_constraints"))
        memory_pressure = signals.get("memory_pressure", 0)

        strategy = proposed_strategy

        # --------------------------------------------------
        # 1. HARD CONSTRAINTS (priority layer)
        # --------------------------------------------------
        if has_constraints:
            if strategy == ResponseStrategyType.ACTION:
                return ResponseStrategyType.CONFIRMATION

        # --------------------------------------------------
        # 2. MEMORY PRESSURE (progressive regulation)
        # --------------------------------------------------
        # Higher memory load → more conservative behavior

        if memory_pressure >= 5:
            if strategy == ResponseStrategyType.ACTION:
                strategy = ResponseStrategyType.CONFIRMATION

        elif memory_pressure >= 3:
            if strategy == ResponseStrategyType.ACTION:
                strategy = ResponseStrategyType.CONFIRMATION

        # --------------------------------------------------
        # 3. DOMAIN-SPECIFIC CONSTRAINTS (extensible)
        # --------------------------------------------------
        # Pattern: declarative constraints → strategy mapping

        if "no_marketing_emails" in constraints:
            if strategy == ResponseStrategyType.ACTION:
                strategy = ResponseStrategyType.CONFIRMATION

        # --------------------------------------------------
        # 4. FUTURE EXTENSION HOOK
        # --------------------------------------------------
        # Example:
        # if "no_autonomous_actions" in constraints:
        #     ...

        return strategy
