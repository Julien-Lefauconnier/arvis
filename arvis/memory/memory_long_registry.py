# arvis/memory/memory_long_registry.py

from dataclasses import dataclass
from typing import Set, Dict, Optional



@dataclass(frozen=True)
class MemoryLongRegistry:
    """
    Registry of allowed long-term memory keys.

    ZKCS rule:
    - no arbitrary user profiling
    - keys must be declared in advance
    """

    allowed_keys: Set[str]

    # Optional whitelist for safe declarative plain values
    allowed_plain_values: Dict[str, Set[str]] | None = None

    def is_allowed(self, key: str) -> bool:
        return key in self.allowed_keys

    def validate_value_plain(
        self,
        *,
        key: str,
        value: Optional[str],
    ) -> bool:
        """
        ZKCS rule:
        value_plain is only allowed for strictly whitelisted keys.
        """

        if value is None:
            return True

        if not self.allowed_plain_values:
            return False

        allowed = self.allowed_plain_values.get(key)
        if not allowed:
            return False

        return value in allowed

# ---------------------------------------------------------
# Default registry (baseline)
# ---------------------------------------------------------

DEFAULT_MEMORY_LONG_KEYS = {
    # Preferences
    "language",
    "preferred_language",
    "tone_style",

    # Context
    "timezone",

    # Constraints
    "no_marketing_emails",

    # System
    "working_mode",
}

DEFAULT_PLAIN_VALUE_WHITELIST = {
    # Preferences
    "language": {"fr", "en", "es", "de"},

    # Context
    "timezone": {"UTC", "Europe/Paris"},
}


DEFAULT_MEMORY_LONG_REGISTRY = MemoryLongRegistry(
    allowed_keys=DEFAULT_MEMORY_LONG_KEYS,
    allowed_plain_values=DEFAULT_PLAIN_VALUE_WHITELIST,
)
