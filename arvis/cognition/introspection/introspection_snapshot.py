# arvis/cognition/introspection/introspection_snapshot.py

from dataclasses import dataclass, field
from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class IntrospectionSnapshot:
    """
    Declarative snapshot of self-observed cognitive limits.

    Kernel guarantees:
    - no reasoning
    - no inference
    - no decision
    """

    active_limits: list[str] = field(default_factory=list)
    active_constraints: list[str] = field(default_factory=list)
    unavailable_capabilities: list[str] = field(default_factory=list)

    notes: str | None = None

    created_at: datetime = field(default_factory=utcnow)

    @classmethod
    def empty(cls) -> "IntrospectionSnapshot":
        """
        Deterministic empty introspection snapshot.
        """
        return cls()
