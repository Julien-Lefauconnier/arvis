# arvis/cognition/decision/decision_context.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionContext:
    """
    Minimal ZKCS-safe context.
    """

    user_id: str
    intent_type: str

    long_memory: dict[str, Any] | None = None
    conversation_mode: str | None = None
