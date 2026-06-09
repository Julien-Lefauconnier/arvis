# tests/telemetry/test_telemetry_redaction.py

from arvis.telemetry import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.redaction import redacted_payload


def _event(attributes: dict[str, object]) -> TelemetryEvent:
    return TelemetryEvent.create(
        kind=TelemetryKind.LIFECYCLE,
        component="kernel.pipeline",
        message="stage finished",
        level=TelemetryLevel.INFO,
        attributes=attributes,
        sequence=1,
    )


def test_redaction_masks_sensitive_keys() -> None:
    event = _event({"api_key": "shhh", "score": 0.9})
    payload = redacted_payload(event)
    assert payload["attributes"] == {"api_key": "<redacted>", "score": 0.9}


def test_redaction_preserves_identity() -> None:
    event = _event({"token": "abc"})
    payload = redacted_payload(event)
    assert payload["fingerprint"] == event.fingerprint
    assert payload["event_id"] == event.event_id


def test_redaction_drops_traceback_by_default() -> None:
    event = _event({"traceback": "stack", "score": 1})
    payload = redacted_payload(event)
    assert "traceback" not in payload["attributes"]  # type: ignore[operator]


def test_redaction_is_noop_on_clean_attributes() -> None:
    event = _event({"score": 0.5, "regime": "stable"})
    payload = redacted_payload(event)
    assert payload["attributes"] == {"score": 0.5, "regime": "stable"}
