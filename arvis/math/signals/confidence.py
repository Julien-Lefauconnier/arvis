# arvis/math/signals/confidence.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.signals.base import BaseSignal


@dataclass(frozen=True)
class ConfidenceSignal(BaseSignal):
    """
    Epistemic confidence signal.
    """

    value: float