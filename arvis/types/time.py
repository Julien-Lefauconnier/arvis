# arvis/types/time.py

from __future__ import annotations

from dataclasses import dataclass


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


# Campaign FINITION (audit #2 P2-4, 2026-09-02): this module used to
# carry a second ``utcnow()`` returning its own WallClockTimestamp
# type, duplicating arvis/types/timestamps.py with a different return
# type and zero consumers. Both dead pieces are deleted; the wall
# clock has exactly one accessor (types/timestamps.py) and this
# module keeps the consumed LogicalTimestamp only.
