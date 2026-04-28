# arvis/cognition/explanation/explanation_snapshot.py

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ExplanationSnapshot:
    """
    Exposable explanation layer.

    Kernel guarantees:
    - declarative
    - non-reasoning
    - zero-knowledge compatible
    """

    items: list[Any] = field(default_factory=list)

    stability: dict[str, Any] = field(default_factory=dict)
    lyapunov: dict[str, Any] = field(default_factory=dict)
    trajectory: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utcnow)

    @classmethod
    def empty(cls) -> "ExplanationSnapshot":
        """
        Deterministic empty explanation snapshot.
        """
        return cls()
