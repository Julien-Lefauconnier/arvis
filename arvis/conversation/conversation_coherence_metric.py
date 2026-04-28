# arvisconversation/conversation_coherence_metric.py

from arvis.conversation.conversation_state import ConversationState


class ConversationCoherenceMetric:
    """
    Computes a coherence score for the dialogue trajectory.
    """

    @staticmethod
    def compute(state: ConversationState) -> float:
        if state.turn_count == 0:
            return 1.0

        streak_factor = state.strategy_streak / (state.turn_count + 1)

        momentum_factor = abs(state.momentum)

        coherence = (streak_factor + (1 - momentum_factor)) / 2

        return max(0.0, min(coherence, 1.0))
