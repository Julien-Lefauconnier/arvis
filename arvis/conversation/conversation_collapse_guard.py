# arvis/conversation/conversation_collapse_guard.py

from typing import Any

from arvis.conversation.conversation_state import (
    ConversationState,
)


class ConversationCollapseGuard:
    """
    Detects conversation collapse risks.
    """

    COLLAPSE_THRESHOLD = 0.75

    @staticmethod
    def detect(state: ConversationState) -> bool:

        raw: Any = state.signals.get("collapse_risk")

        if not isinstance(raw, (int, float)):
            return False

        collapse_risk = float(raw)

        return collapse_risk >= ConversationCollapseGuard.COLLAPSE_THRESHOLD