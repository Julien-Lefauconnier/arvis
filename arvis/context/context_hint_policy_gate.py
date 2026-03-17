# arvis/context/context_hint_policy_gate.py

from dataclasses import dataclass
from typing import Dict, Any, Set


@dataclass(frozen=True)
class ContextHintPolicyGate:
    """
    ZKCS-safe governance gate for context hints.
    """

    ALLOWED_KEYS: Set[str] = frozenset({
        "preferred_language",
        "timezone",
    })

    @classmethod
    def validate(cls, hints: Dict[str, Any]) -> Dict[str, Any]:

        safe = {}

        for key, value in hints.items():

            if key not in cls.ALLOWED_KEYS:
                continue

            if isinstance(value, (str, bool, int, float)):
                safe[key] = value

        return safe