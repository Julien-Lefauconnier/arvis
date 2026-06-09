# tests/telemetry/test_telemetry_forecast_adapter.py

from arvis.math.observability.global_forecast_snapshot import GlobalForecastSnapshot
from arvis.telemetry import TelemetryKind
from arvis.telemetry.adapters import FORECAST_COMPONENT, forecast_event


def test_forecast_event_maps_fields() -> None:
    event = forecast_event(
        GlobalForecastSnapshot(
            predicted_mean_delta=0.03,
            slope=0.01,
            collapse_risk=0.12,
            time_to_critical=None,
            early_warning=False,
        )
    )
    assert event.kind is TelemetryKind.STABILITY
    assert event.component == FORECAST_COMPONENT
    assert event.attributes["predicted_mean_delta"] == 0.03
    assert event.attributes["slope"] == 0.01
    assert event.attributes["collapse_risk"] == 0.12
    assert event.attributes["time_to_critical"] is None
    assert event.attributes["early_warning"] is False


def test_forecast_event_early_warning_and_ttc() -> None:
    event = forecast_event(
        GlobalForecastSnapshot(
            predicted_mean_delta=0.5,
            slope=0.2,
            collapse_risk=0.9,
            time_to_critical=8.0,
            early_warning=True,
        )
    )
    assert event.attributes["early_warning"] is True
    assert event.attributes["time_to_critical"] == 8.0
