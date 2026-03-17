# arvis/cognition/control/adaptive_mode_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveModeSnapshot:
    """
    Declarative adaptive cognition mode.

    Kernel invariants:
    - immutable
    - no dynamic evaluation
    """

    risk: float
    mode: str