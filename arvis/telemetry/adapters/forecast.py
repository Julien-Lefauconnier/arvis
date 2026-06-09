# arvis/telemetry/adapters/forecast.py

from __future__ import annotations

from arvis.math.observability.global_forecast_snapshot import GlobalForecastSnapshot
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

FORECAST_COMPONENT = "kernel.forecast"


def forecast_event(
    snapshot: GlobalForecastSnapshot,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = FORECAST_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a telemetry event from the global forecast snapshot.

    ``GlobalForecastSnapshot`` projects the global stability trajectory: the
    predicted mean delta, its slope, the collapse risk, an optional estimated
    time-to-critical and an early-warning flag. All values are deterministic
    and ZKCS-safe.
    """
    attributes: TelemetryAttributes = {
        "predicted_mean_delta": snapshot.predicted_mean_delta,
        "slope": snapshot.slope,
        "collapse_risk": snapshot.collapse_risk,
        "time_to_critical": snapshot.time_to_critical,
        "early_warning": snapshot.early_warning,
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="global forecast snapshot",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
