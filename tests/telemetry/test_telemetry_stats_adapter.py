# tests/telemetry/test_telemetry_stats_adapter.py

from arvis.math.observability.stability_stats_snapshot import StabilityStatsSnapshot
from arvis.telemetry import TelemetryKind
from arvis.telemetry.adapters import STATS_COMPONENT, stats_event


def test_stats_event_maps_fields() -> None:
    event = stats_event(
        StabilityStatsSnapshot(
            mean_delta=0.02,
            contraction_rate=0.88,
            instability_rate=0.05,
            samples=42,
        )
    )
    assert event.kind is TelemetryKind.STABILITY
    assert event.component == STATS_COMPONENT
    assert event.attributes["mean_delta"] == 0.02
    assert event.attributes["contraction_rate"] == 0.88
    assert event.attributes["instability_rate"] == 0.05
    assert event.attributes["samples"] == 42


def test_stats_event_zero_samples() -> None:
    event = stats_event(
        StabilityStatsSnapshot(
            mean_delta=0.0,
            contraction_rate=1.0,
            instability_rate=0.0,
            samples=0,
        )
    )
    assert event.attributes["samples"] == 0
    assert event.attributes["contraction_rate"] == 1.0
