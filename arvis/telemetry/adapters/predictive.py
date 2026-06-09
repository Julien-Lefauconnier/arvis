# arvis/telemetry/adapters/predictive.py

from __future__ import annotations

from arvis.math.observability.predictive_snapshot import PredictiveSnapshot
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

PREDICTIVE_COMPONENT = "kernel.predictive"


def predictive_event(
    snapshot: PredictiveSnapshot,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = PREDICTIVE_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a telemetry event from the predictive stability snapshot.

    ``PredictiveSnapshot`` projects the short-horizon trajectory of the
    Lyapunov signal: the predicted value, its slope, an optional estimated
    time-to-critical, the gate verdict that produced it and the horizon.
    All values are deterministic and ZKCS-safe.
    """
    attributes: TelemetryAttributes = {
        "predicted_v": snapshot.predicted_v,
        "slope": snapshot.slope,
        "time_to_critical": snapshot.time_to_critical,
        "verdict": snapshot.verdict,
        "horizon": snapshot.horizon,
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="predictive snapshot",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
