# arvis/cognition/conversation/response_realization_mode.py

from enum import Enum


class ResponseRealizationMode(str, Enum):
    """
    How a response is produced.
    """

    TEMPLATE = "template"
    LLM = "llm"
    HYBRID = "hybrid"
