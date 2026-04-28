# arvis/math/signals/base.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsFloat(Protocol):
    def __float__(self) -> float: ...


@dataclass(frozen=True)
class BaseSignal:
    """
    Base abstraction for all cognitive signals.

    Guarantees:
    - normalized [0,1] (enforced by subclasses)
    - immutable
    - float-compatible
    """

    value: float

    # -----------------------------------------
    # Core API
    # -----------------------------------------

    def level(self) -> float:
        return self.value

    def __float__(self) -> float:
        return self.value

    # -----------------------------------------
    # Comparators (critical for migration)
    # -----------------------------------------

    def __lt__(self, other: float | SupportsFloat) -> bool:
        return self.value < float(other)

    def __le__(self, other: float | SupportsFloat) -> bool:
        return self.value <= float(other)

    def __gt__(self, other: float | SupportsFloat) -> bool:
        return self.value > float(other)

    def __ge__(self, other: float | SupportsFloat) -> bool:
        return self.value >= float(other)

    def __eq__(self, other: object) -> bool:
        try:
            return self.value == float(other)  # type: ignore[arg-type]
        except Exception:
            return False

    # -----------------------------------------
    # Utility
    # -----------------------------------------

    def is_zero(self) -> bool:
        return self.value == 0.0

    def is_max(self) -> bool:
        return self.value == 1.0
