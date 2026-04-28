# arvis/conversation/conversation_lyapunov_adapter.py

from arvis.conversation.conversation_state import (
    ConversationState,
)

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class ConversationLyapunovAdapter:
    """
    Bridges Lyapunov math stability to conversation strategy control.
    """

    @staticmethod
    def extract_verdict(state: ConversationState) -> LyapunovVerdict | None:
        verdict = state.signals.get("lyapunov_verdict")

        if verdict is None:
            return None

        try:
            return LyapunovVerdict(verdict)
        except Exception:
            return None
