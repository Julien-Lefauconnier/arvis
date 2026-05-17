# arvis/types/time.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, order=True)
class LogicalTimestamp:
    """
    Deterministic monotonic runtime timestamp.

    Used for:
    - scheduler ordering
    - replay ordering
    - runtime signal sequencing
    - causal deterministic execution

    MUST NOT depend on wall-clock time.
    """

    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("LogicalTimestamp must be >= 0")


@dataclass(frozen=True)
class WallClockTimestamp:
    """
    Real UTC wall-clock timestamp.

    Used for:
    - observability
    - audit logs
    - external tracing
    - telemetry export
    """

    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo != UTC:
            raise ValueError("WallClockTimestamp must be UTC-aware")


def utcnow() -> WallClockTimestamp:
    return WallClockTimestamp(datetime.now(UTC))
