# arvis/cognition/pending/pending_cognitive_action.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PendingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PendingCognitiveAction:
    """
    Represents a deferred cognitive decision.

    Kernel invariants:
    - immutable
    - declarative
    - no execution
    """

    bundle_id: str
    user_id: str
    created_at: datetime
    status: PendingStatus
