# arvis/cognition/conversation/conversation_mode.py

from enum import Enum


class ConversationMode(str, Enum):
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