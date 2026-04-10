# arvis/conversation/conversation_adversarial_detector.py

from arvis.conversation.response_strategy_type import (
    ResponseStrategyType,
)


class ConversationAdversarialDetector:
    """
    Detects adversarial conversational patterns.
    """

    ADVERSARIAL_THRESHOLD = 0.7

    @staticmethod
    def detect(
        *,
        prompt: str,
        collapse_risk: float | None,
        uncertainty: float | None,
    ) -> float:

        score = 0.0

        if collapse_risk:
            score += collapse_risk * 0.5

        if uncertainty:
            score += uncertainty * 0.5

        if prompt:
            lowered = prompt.lower()

            suspicious_patterns = [
                "ignore previous",
                "you must answer",
                "override instructions",
                "do not refuse",
            ]

            if any(p in lowered for p in suspicious_patterns):
                score += 0.5

        return min(score, 1.0)

    @staticmethod
    def regulate(
        *,
        strategy: ResponseStrategyType,
        adversarial_score: float,
    ) -> ResponseStrategyType:

        if adversarial_score > ConversationAdversarialDetector.ADVERSARIAL_THRESHOLD:
            return ResponseStrategyType.CONFIRMATION

        return strategy