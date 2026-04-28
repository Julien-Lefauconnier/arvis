# arvis/control/understanding_snapshot.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class UnderstandingState(str, Enum):
    INITIAL = "initial"
    FRAGILE = "fragile"
    ADJUSTING = "adjusting"
    STABLE = "stable"


class UnderstandingTrend(str, Enum):
    UP = "up"
    STABLE = "stable"
    DOWN = "down"


@dataclass(frozen=True)
class UnderstandingSnapshot:
    """
    Declarative understanding alignment snapshot.
    """

    state: UnderstandingState
    trend: Optional[UnderstandingTrend] = None

    active_uncertainties: List[str] = field(default_factory=list)
    active_conflicts: List[str] = field(default_factory=list)
    active_reasoning_intents: List[str] = field(default_factory=list)

    notes: Optional[str] = None
    created_at: Optional[datetime] = None
