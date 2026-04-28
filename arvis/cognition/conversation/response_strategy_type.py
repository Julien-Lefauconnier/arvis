# arvis/cognition/conversation/response_strategy_type.py

from enum import StrEnum


class ResponseStrategyType(StrEnum):
    """
    High-level conversational response strategy.

    Kernel invariants:
    - describes nature of response
    - independent of realization (LLM, template, etc.)
    """

    SOCIAL = "social"
    INFORMATIONAL = "informational"
    ACTION = "action"
    CONFIRMATION = "confirmation"
    ABSTENTION = "abstention"
    META = "meta"
