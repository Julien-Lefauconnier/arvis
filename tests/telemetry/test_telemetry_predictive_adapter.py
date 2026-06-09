# tests/telemetry/test_telemetry_predictive_adapter.py

from arvis.math.observability.predictive_snapshot import PredictiveSnapshot
from arvis.telemetry import TelemetryKind
from arvis.telemetry.adapters import PREDICTIVE_COMPONENT, predictive_event


def test_predictive_event_maps_fields() -> None:
    event = predictive_event(
        PredictiveSnapshot(
            predicted_v=0.42,
            slope=0.01,
            time_to_critical=None,
            verdict="ALLOW",
            horizon=5,
        )
    )
    assert event.kind is TelemetryKind.STABILITY
    assert event.component == PREDICTIVE_COMPONENT
    assert event.attributes["predicted_v"] == 0.42
    assert event.attributes["slope"] == 0.01
    assert event.attributes["time_to_critical"] is None
    assert event.attributes["verdict"] == "ALLOW"
    assert event.attributes["horizon"] == 5


def test_predictive_event_defaults_horizon_none() -> None:
    event = predictive_event(
        PredictiveSnapshot(
            predicted_v=0.0,
            slope=0.0,
            time_to_critical=12.0,
            verdict=None,
        )
    )
    assert event.attributes["horizon"] is None
    assert event.attributes["time_to_critical"] == 12.0
