# arvis/math/signals/forecast.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.signals.base import BaseSignal


@dataclass(frozen=True)
class ForecastSignal(BaseSignal):
    """
    Predictive / forecast strength signal.
    """

    value: float