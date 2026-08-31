# arvis/stability/__init__.py
"""
Stability observer interfaces.

Defines contracts for stability observers used by
ARVIS-compatible systems.

The snapshot dataclasses (PredictiveSnapshot, MultiHorizonSnapshot,
GlobalForecastSnapshot) live in ``arvis.math.observability``; this
package used to carry byte-identical duplicates of them (audit A4,
2026-08). They stay re-exported here so the public import path is
stable.
"""

from arvis.math.observability.global_forecast_snapshot import (
    GlobalForecastSnapshot,
)
from arvis.math.observability.multi_horizon_snapshot import (
    MultiHorizonSnapshot,
)
from arvis.math.observability.predictive_snapshot import PredictiveSnapshot

from .stability_observer import StabilityObserver, StabilitySnapshot

__all__ = [
    "StabilityObserver",
    "StabilitySnapshot",
    "GlobalForecastSnapshot",
    "MultiHorizonSnapshot",
    "PredictiveSnapshot",
]
