# tests/telemetry/test_telemetry_stability_adapter.py

from arvis.stability.stability_snapshot import StabilitySnapshot
from arvis.telemetry import TelemetryKind, TelemetryLevel
from arvis.telemetry.adapters import STABILITY_COMPONENT, stability_event


def _snapshot() -> StabilitySnapshot:
    return StabilitySnapshot(
        verdict="OK",
        score=0.91,
        confidence=0.8,
        samples=42,
        mean_dv=0.01,
        std_dv=0.02,
        instability_rate=0.03,
        collapse_risk=0.12,
        last_v=0.44,
        reasons=["within bounds"],
    )


def test_stability_event_maps_all_math_fields() -> None:
    event = stability_event(_snapshot())
    assert event.kind is TelemetryKind.STABILITY
    assert event.level is TelemetryLevel.INFO
    assert event.component == STABILITY_COMPONENT
    assert event.attributes["verdict"] == "OK"
    assert event.attributes["score"] == 0.91
    assert event.attributes["collapse_risk"] == 0.12
    assert event.attributes["last_v"] == 0.44
    assert event.attributes["instability_rate"] == 0.03
    assert event.attributes["reasons"] == ["within bounds"]


def test_level_is_caller_supplied() -> None:
    event = stability_event(_snapshot(), level=TelemetryLevel.WARNING)
    assert event.level is TelemetryLevel.WARNING


def test_reasons_are_copied_not_shared() -> None:
    reasons = ["a", "b"]
    snapshot = StabilitySnapshot(
        verdict="WARN",
        score=0.5,
        confidence=0.5,
        samples=1,
        mean_dv=0.0,
        std_dv=0.0,
        instability_rate=0.0,
        collapse_risk=0.7,
        last_v=0.9,
        reasons=reasons,
    )
    event = stability_event(snapshot)
    reasons.append("mutated")
    assert event.attributes["reasons"] == ["a", "b"]


def test_fingerprint_is_deterministic() -> None:
    a = stability_event(_snapshot(), sequence=1)
    b = stability_event(_snapshot(), sequence=1)
    assert a.event_id == b.event_id


def test_custom_component_and_sequence() -> None:
    event = stability_event(_snapshot(), component="os.stability", sequence=7)
    assert event.component == "os.stability"
    assert event.sequence == 7
