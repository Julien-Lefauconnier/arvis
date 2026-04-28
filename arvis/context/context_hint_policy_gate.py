# arvis/context/context_hint_policy_gate.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContextHintPolicyGate:
    """
    ZKCS-safe governance gate for context hints.
    """

    ALLOWED_KEYS: frozenset[str] = frozenset(
        {
            "preferred_language",
            "timezone",
        }
    )

    @classmethod
    def validate(cls, hints: dict[str, Any]) -> dict[str, Any]:
        safe: dict[str, Any] = {}

        for key, value in hints.items():
            if key not in cls.ALLOWED_KEYS:
                continue

            if isinstance(value, (str, bool, int, float)):
                safe[key] = value

        return safe
