# arvis/api/stability.py

"""
Public stability interfaces and snapshots.
"""

from dataclasses import dataclass

from arvis.stability.global_forecast_snapshot import GlobalForecastSnapshot
from arvis.stability.multi_horizon_snapshot import MultiHorizonSnapshot
from arvis.stability.predictive_snapshot import PredictiveSnapshot
from arvis.stability.stability_observer import (
    StabilityObserver,
    StabilitySnapshot,
)

# -----------------------------------------------------
# Public simplified view (API-level)
# -----------------------------------------------------


@dataclass(frozen=True)
class StabilityView:
    """
    Lightweight stability view for external consumers.

    Every axis is optional: an axis the run did not measure is reported
    as ``None``, never as a fabricated ``0.0`` or the string ``"None"``.
    On the input-risk path (an explicit ``{"risk": x}`` payload) the
    stability axes are not computed at all, so a view full of zeros was
    reporting measurements that never happened (audit C5, 2026-08). The
    consumer contract (``cognitive_result_v1.schema.json``) has always
    allowed ``null`` here.
    """

    stability_score: float | None
    risk_level: float | None
    regime: str | None

    @staticmethod
    def from_snapshot(snapshot: StabilitySnapshot) -> "StabilityView":
        def _number(*names: str) -> float | None:
            for name in names:
                value = getattr(snapshot, name, None)
                if value is not None:
                    return float(value)
            return None

        regime = getattr(snapshot, "verdict", None)
        if regime is None:
            regime = getattr(snapshot, "regime", None)

        # A snapshot that reached no conclusion (neither a regime nor a
        # stability verdict) carries constructor defaults in its numeric
        # fields, not measurements: report the whole view as absent
        # rather than dressing defaults up as data.
        if regime is None and getattr(snapshot, "stable", None) is None:
            return StabilityView(
                stability_score=None,
                risk_level=None,
                regime=None,
            )

        return StabilityView(
            stability_score=_number("score", "stability_score"),
            risk_level=_number("collapse_risk", "risk"),
            regime=str(regime) if regime is not None else None,
        )


__all__ = [
    "StabilityObserver",
    "StabilitySnapshot",
    "GlobalForecastSnapshot",
    "MultiHorizonSnapshot",
    "PredictiveSnapshot",
    "StabilityView",
]
