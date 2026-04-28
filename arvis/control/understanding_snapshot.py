# arvis/control/understanding_snapshot.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class UnderstandingState(StrEnum):
    INITIAL = "initial"
    FRAGILE = "fragile"
    ADJUSTING = "adjusting"
    STABLE = "stable"


class UnderstandingTrend(StrEnum):
    UP = "up"
    STABLE = "stable"
    DOWN = "down"


@dataclass(frozen=True)
class UnderstandingSnapshot:
    """
    Declarative understanding alignment snapshot.
    """

    state: UnderstandingState
    trend: UnderstandingTrend | None = None

    active_uncertainties: list[str] = field(default_factory=list)
    active_conflicts: list[str] = field(default_factory=list)
    active_reasoning_intents: list[str] = field(default_factory=list)

    notes: str | None = None
    created_at: datetime | None = None
