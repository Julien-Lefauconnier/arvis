# arvis/api/stability.py

"""
Public stability interfaces and snapshots.
"""

from dataclasses import dataclass

from arvis.math.core.normalization import clamp01
from arvis.math.observability.global_forecast_snapshot import (
    GlobalForecastSnapshot,
)
from arvis.math.observability.multi_horizon_snapshot import (
    MultiHorizonSnapshot,
)
from arvis.math.observability.predictive_snapshot import PredictiveSnapshot
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

    ``risk_level`` is the EMPIRICAL collapse rate (what has been
    observed so far) and ``risk_ucb`` is the CERTIFIED PAC ceiling
    (what can be ruled out so far); on a cold turn they legitimately
    read 0.0 and 1.0 at once, and hiding the ceiling made calm out of
    maximal uncertainty (campaign INTEGRITY, DM-I3, audit P1-6).
    """

    stability_score: float | None
    risk_level: float | None
    regime: str | None
    risk_ucb: float | None = None
    risk_verdict: str | None = None

    @staticmethod
    def from_snapshot(snapshot: StabilitySnapshot) -> "StabilityView":
        def _number(*names: str) -> float | None:
            for name in names:
                value = getattr(snapshot, name, None)
                if value is not None:
                    return float(value)
            return None

        def _inner_number(name: str) -> float | None:
            value = getattr(snapshot, name, None)
            if value is None:
                inner = getattr(snapshot, "core_snapshot", None)
                value = getattr(inner, name, None) if inner is not None else None
            if value is None or isinstance(value, bool):
                return None
            return float(value) if isinstance(value, (int, float)) else None

        def _inner_text(name: str) -> str | None:
            value = getattr(snapshot, name, None)
            if value is None:
                inner = getattr(snapshot, "core_snapshot", None)
                value = getattr(inner, name, None) if inner is not None else None
            return str(value) if value is not None else None

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

        # A measured Lyapunov energy V (in [0, 1]) defines the score as
        # its complement: stability_score = 1 - V. The energy lives on
        # the embedded core snapshot when the scientific result wraps a
        # monitor snapshot (campaign MATH-A, M1). The PAC risk ceiling
        # and its calibrated verdict live on the same core snapshot.
        score = _number("score", "stability_score")
        if score is None:
            inner = getattr(snapshot, "core_snapshot", None)
            energy = getattr(inner, "energy_v", None) if inner is not None else None
            if energy is None:
                energy = getattr(snapshot, "energy_v", None)
            if energy is not None:
                score = 1.0 - clamp01(float(energy))

        return StabilityView(
            stability_score=score,
            risk_level=_number("collapse_risk", "risk"),
            regime=str(regime) if regime is not None else None,
            risk_ucb=_inner_number("risk_ucb"),
            risk_verdict=_inner_text("risk_verdict"),
        )


__all__ = [
    "StabilityObserver",
    "StabilitySnapshot",
    "GlobalForecastSnapshot",
    "MultiHorizonSnapshot",
    "PredictiveSnapshot",
    "StabilityView",
]
