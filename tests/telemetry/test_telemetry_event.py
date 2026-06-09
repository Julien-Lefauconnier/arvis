# tests/telemetry/test_telemetry_event.py

from datetime import UTC, datetime

import pytest

from arvis.telemetry import (
    TelemetryEvent,
    TelemetryKind,
    TelemetryLevel,
)


def _event(**overrides: object) -> TelemetryEvent:
    kwargs: dict[str, object] = {
        "kind": TelemetryKind.STABILITY,
        "level": TelemetryLevel.INFO,
        "component": "kernel.gate",
        "message": "stability evaluated",
        "attributes": {"score": 0.42, "regime": "unstable"},
    }
    kwargs.update(overrides)
    return TelemetryEvent(**kwargs)  # type: ignore[arg-type]


def test_fingerprint_is_deterministic_for_identical_content() -> None:
    a = _event()
    b = _event()
    assert a.fingerprint == b.fingerprint
    assert len(a.fingerprint) == 64


def test_identity_excludes_wall_clock_and_monotonic() -> None:
    early = datetime(2020, 1, 1, tzinfo=UTC)
    late = datetime(2030, 6, 9, tzinfo=UTC)
    a = _event(emitted_at=early, monotonic_ns=1)
    b = _event(emitted_at=late, monotonic_ns=999)
    assert a.event_id == b.event_id
    assert a.fingerprint == b.fingerprint


def test_event_id_equals_fingerprint_without_sequence() -> None:
    event = _event()
    assert event.sequence is None
    assert event.event_id == event.fingerprint


def test_event_id_depends_on_sequence() -> None:
    first = _event(sequence=1)
    second = _event(sequence=2)
    assert first.event_id != second.event_id
    assert first.fingerprint == second.fingerprint


def test_fingerprint_changes_with_content() -> None:
    base = _event()
    other = _event(attributes={"score": 0.99, "regime": "stable"})
    assert base.fingerprint != other.fingerprint


def test_to_dict_shape() -> None:
    event = _event(sequence=3)
    payload = event.to_dict()
    assert payload["kind"] == "stability"
    assert payload["level"] == "info"
    assert payload["component"] == "kernel.gate"
    assert payload["sequence"] == 3
    assert payload["attributes"] == {"score": 0.42, "regime": "unstable"}
    assert payload["fingerprint"] == event.fingerprint
    assert payload["event_id"] == event.event_id
    assert isinstance(payload["emitted_at"], str)


def test_create_fills_emitted_at_and_monotonic() -> None:
    event = TelemetryEvent.create(
        kind=TelemetryKind.DECISION,
        component="kernel.pipeline",
        message="gate resolved",
    )
    assert event.level is TelemetryLevel.INFO
    assert event.monotonic_ns is not None
    assert event.emitted_at.tzinfo is not None
    assert event.attributes == {}


def test_empty_component_is_rejected() -> None:
    with pytest.raises(ValueError, match="component"):
        _event(component="")


def test_event_is_frozen() -> None:
    event = _event()
    with pytest.raises(AttributeError):
        event.component = "mutated"  # type: ignore[misc]


def test_timestamp_property_returns_emitted_at() -> None:
    moment = datetime(2026, 6, 9, 12, 0, tzinfo=UTC)
    event = _event(emitted_at=moment)
    assert event.timestamp == moment
