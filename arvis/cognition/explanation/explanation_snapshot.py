# arvis/cognition/explanation/explanation_snapshot.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ExplanationSnapshot:
    """
    Exposable explanation layer.

    Kernel guarantees:
    - declarative
    - non-reasoning
    - zero-knowledge compatible
    """

    items: List[Any] = field(default_factory=list)

    stability: Dict[str, Any] = field(default_factory=dict)
    lyapunov: Dict[str, Any] = field(default_factory=dict)
    trajectory: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utcnow)

    @classmethod
    def empty(cls) -> "ExplanationSnapshot":
        """
        Deterministic empty explanation snapshot.
        """
        return cls()
