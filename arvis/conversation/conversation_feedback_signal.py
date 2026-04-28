# arvis/conversation/conversation_feedback_signal.py

from typing import Any, Dict


class ConversationFeedbackSignal:
    """
    Builds lightweight feedback signals from conversation outcome.

    ZKCS-safe:
    - no payload storage
    - no user content
    - only structural signals
    """

    @staticmethod
    def build(state: Any) -> Dict[str, Any]:
        signals = state.signals or {}

        strategy = getattr(state, "last_strategy", None)

        return {
            "was_action": strategy.value == "action" if strategy else False,
            "high_uncertainty": signals.get("uncertainty", 0) > 0.6,
            "high_collapse_risk": signals.get("collapse_risk", 0) > 0.6,
            "energy": signals.get("energy"),
        }
