# arvis/reasoning/reasoning_intent.py
from dataclasses import dataclass
from enum import Enum, auto


class ReasoningIntentType(Enum):
    """
    Declarative types describing what the system
    suggests to do because of a reasoning gap.
    """

    REQUEST_USER_CLARIFICATION = auto()
    DEFER_ACTION = auto()
    BLOCK_IRREVERSIBLE_ACTION = auto()
    ALLOW_WEAK_ASSUMPTION = auto()


@dataclass(frozen=True)
class ReasoningIntent:
    """
    Declarative reasoning suggestion.

    ⚠️ This object:
    - does NOT act
    - does NOT decide
    - does NOT execute
    """

    intent_type: ReasoningIntentType
    reason: str
    # 🧭 Declarative traceability (what triggered this intent)
    source_ref: str | None = None
