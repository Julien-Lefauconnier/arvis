# arvis/cognition/decision/decision_context.py

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class DecisionContext:
    """
    Minimal ZKCS-safe context.
    """

    user_id: str
    intent_type: str

    long_memory: Optional[Dict[str, Any]] = None
    conversation_mode: Optional[str] = None