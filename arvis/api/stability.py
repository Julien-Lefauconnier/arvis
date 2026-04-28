# arvis/api/stability.py

"""
Public stability interfaces and snapshots.
"""

from dataclasses import dataclass

from arvis.stability.stability_observer import (
    StabilityObserver,
    StabilitySnapshot,
)

from arvis.stability.global_forecast_snapshot import GlobalForecastSnapshot
from arvis.stability.multi_horizon_snapshot import MultiHorizonSnapshot
from arvis.stability.predictive_snapshot import PredictiveSnapshot

# -----------------------------------------------------
# Public simplified view (API-level)
# -----------------------------------------------------


@dataclass(frozen=True)
class StabilityView:
    """
    Lightweight stability view for external consumers.
    """

    stability_score: float
    risk_level: float
    regime: str

    @staticmethod
    def from_snapshot(snapshot: StabilitySnapshot) -> "StabilityView":
        return StabilityView(
            stability_score=getattr(
                snapshot, "score", getattr(snapshot, "stability_score", 0.0)
            ),
            risk_level=getattr(
                snapshot, "collapse_risk", getattr(snapshot, "risk", 0.0)
            ),
            regime=str(
                getattr(snapshot, "verdict", getattr(snapshot, "regime", "unknown"))
            ),
        )


__all__ = [
    "StabilityObserver",
    "StabilitySnapshot",
    "GlobalForecastSnapshot",
    "MultiHorizonSnapshot",
    "PredictiveSnapshot",
    "StabilityView",
]
