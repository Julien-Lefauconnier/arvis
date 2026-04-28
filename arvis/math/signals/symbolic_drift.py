# arvis/math/signals/symbolic_drift.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.signals.base import BaseSignal


@dataclass(frozen=True)
class SymbolicDriftSignal(BaseSignal):
    """
    Symbolic inconsistency / contradiction pressure signal.
    """

    value: float
