# arvis/cognition/conversation/response_realization_mode.py

from enum import StrEnum


class ResponseRealizationMode(StrEnum):
    """
    How a response is produced.
    """

    TEMPLATE = "template"
    LLM = "llm"
    HYBRID = "hybrid"
