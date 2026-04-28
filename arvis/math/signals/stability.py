# arvis/math/signals/stability.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.signals.base import BaseSignal


@dataclass(frozen=True)
class StabilitySignal(BaseSignal):
    """
    Global system stability score.

    Convention:
    - 1.0 = fully stable
    - 0.0 = collapse / no stability
    """

    value: float
