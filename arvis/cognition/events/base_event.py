# arvis/cognition/events/base_event.py

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class BaseEvent:
    """
    Generic cognitive event.

    Kernel invariants:
    - immutable
    - declarative
    - no side effects
    """

    type: str
    user_id: str
    timestamp: datetime
    payload: dict[str, Any]
