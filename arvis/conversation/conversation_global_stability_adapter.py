# arvis/conversation/conversation_global_stability_adapter.py

from typing import Any

from arvis.conversation.conversation_state import (
    ConversationState,
)


class ConversationGlobalStabilityAdapter:
    """
    Bridges global cognitive stability signals
    into the conversation layer.
    """

    @staticmethod
    def extract_verdict(state: ConversationState) -> str | None:
        raw: Any = state.signals.get("global_stability_verdict")

        if raw is None:
            return None

        if not isinstance(raw, str):
            return None

        if raw not in {"OK", "WARN", "CRITICAL"}:
            return None

        return raw
