# arvis/memory/memory_long_policy_gate.py

from datetime import UTC, datetime, timedelta

from arvis.memory.memory_long_entry import (
    MemoryLongEntry,
)
from arvis.memory.memory_long_registry import (
    DEFAULT_MEMORY_LONG_REGISTRY,
    MemoryLongRegistry,
)


class MemoryLongPolicyGate:
    """
    PolicyGate for long-term memory append operations.

    Guarantees:
    - declarative only
    - no arbitrary keys
    - controlled TTL
    - notes are system-only
    """

    MAX_TTL_DAYS = 30

    # Only system-generated tags allowed
    ALLOWED_NOTES = {
        "ttl_default",
        "policy_gate",
        "governance_trace",
    }

    def __init__(
        self,
        registry: MemoryLongRegistry = DEFAULT_MEMORY_LONG_REGISTRY,
    ):
        self.registry = registry

    def validate_append(self, entry: MemoryLongEntry) -> None:
        """
        Validate whether an entry is allowed.

        Raises ValueError if refused.
        """

        # -------------------------------------------------
        # Key must be declared in registry
        # -------------------------------------------------
        if not self.registry.is_allowed(entry.key):
            raise ValueError(f"MemoryLong key '{entry.key}' is not allowed")

        # -------------------------------------------------
        # Source must be explicit or governance-approved
        # -------------------------------------------------
        if entry.source not in {"explicit_user", "onboarding", "governance"}:
            raise ValueError(f"Invalid memory_long source: {entry.source}")

        # -------------------------------------------------
        # Type must exist
        # -------------------------------------------------
        if entry.memory_type is None:
            raise ValueError("memory_type is required")

        # -------------------------------------------------
        # TTL bounded (no uncontrolled persistence)
        # -------------------------------------------------
        if entry.expires_at is not None:
            now = datetime.now(UTC)
            max_allowed = now + timedelta(days=self.MAX_TTL_DAYS)

            if entry.expires_at > max_allowed:
                raise ValueError(
                    f"expires_at exceeds max TTL of {self.MAX_TTL_DAYS} days"
                )

        # -------------------------------------------------
        # Notes must be system-only
        # -------------------------------------------------
        if entry.notes is not None:
            if entry.notes not in self.ALLOWED_NOTES:
                raise ValueError("notes field is system-only and must be whitelisted")

        # -------------------------------------------------
        # value_plain must be strictly whitelisted (ZK-safe)
        # -------------------------------------------------
        value_plain = getattr(entry, "value_plain", None)

        if value_plain is not None:
            if not self.registry.validate_value_plain(
                key=entry.key,
                value=value_plain,
            ):
                raise ValueError(f"value_plain not allowed for key={entry.key}")

        # Declarative only
        return
