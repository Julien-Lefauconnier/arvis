# arvis/cognition/introspection/introspection_snapshot.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class IntrospectionSnapshot:
    """
    Declarative snapshot of self-observed cognitive limits.

    Kernel guarantees:
    - no reasoning
    - no inference
    - no decision
    """

    active_limits: List[str] = field(default_factory=list)
    active_constraints: List[str] = field(default_factory=list)
    unavailable_capabilities: List[str] = field(default_factory=list)

    notes: Optional[str] = None

    created_at: datetime = field(default_factory=utcnow)