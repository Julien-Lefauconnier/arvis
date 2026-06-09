# tests/telemetry/test_telemetry_tension_adapter.py

from arvis.math.signals.system_tension import SystemTensionSignal
from arvis.telemetry import TelemetryKind
from arvis.telemetry.adapters import SYSTEM_TENSION_COMPONENT, system_tension_event


def test_tension_event_maps_axes_and_derived() -> None:
    event = system_tension_event(
        SystemTensionSignal(collapse=0.2, drift=0.6, conflict=0.1)
    )
    assert event.kind is TelemetryKind.STABILITY
    assert event.component == SYSTEM_TENSION_COMPONENT
    assert event.attributes["collapse"] == 0.2
    assert event.attributes["drift"] == 0.6
    assert event.attributes["conflict"] == 0.1
    assert event.attributes["level"] == 0.6
    assert event.attributes["dominant_axis"] == "drift"
    assert event.attributes["is_high"] is False


def test_tension_high_flag_and_dominant_collapse() -> None:
    event = system_tension_event(
        SystemTensionSignal(collapse=0.8, drift=0.1, conflict=0.1)
    )
    assert event.attributes["dominant_axis"] == "collapse"
    assert event.attributes["is_high"] is True
    assert event.attributes["level"] == 0.8
