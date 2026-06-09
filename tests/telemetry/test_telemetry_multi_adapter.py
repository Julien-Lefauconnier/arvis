# tests/telemetry/test_telemetry_multi_adapter.py

from arvis.math.observability.multi_horizon_snapshot import MultiHorizonSnapshot
from arvis.telemetry import TelemetryKind
from arvis.telemetry.adapters import MULTI_HORIZON_COMPONENT, multi_horizon_event


def test_multi_horizon_event_maps_fields() -> None:
    event = multi_horizon_event(
        MultiHorizonSnapshot(
            collapse_risk=0.12,
            stability_confidence=0.88,
            early_warning=False,
            mode_hint="steady",
        )
    )
    assert event.kind is TelemetryKind.STABILITY
    assert event.component == MULTI_HORIZON_COMPONENT
    assert event.attributes["collapse_risk"] == 0.12
    assert event.attributes["stability_confidence"] == 0.88
    assert event.attributes["early_warning"] is False
    assert event.attributes["mode_hint"] == "steady"


def test_multi_horizon_event_defaults_mode_hint_none() -> None:
    event = multi_horizon_event(
        MultiHorizonSnapshot(
            collapse_risk=0.8,
            stability_confidence=0.2,
            early_warning=True,
        )
    )
    assert event.attributes["mode_hint"] is None
    assert event.attributes["early_warning"] is True
