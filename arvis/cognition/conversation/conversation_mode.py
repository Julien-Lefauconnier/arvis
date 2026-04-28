# arvis/cognition/conversation/conversation_mode.py

from enum import StrEnum


class ConversationMode(StrEnum):
    """
    Defines the global conversational regime.

    Kernel invariants:
    - declarative only
    - no LLM directive
    - no execution
    """

    DEFAULT = "default"
    AUDIT = "audit"
    GOVERNANCE = "governance"
    RESTRICTED = "restricted"
