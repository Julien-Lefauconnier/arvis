# tests/telemetry/test_telemetry_errors_adapter.py

from arvis.telemetry import TelemetryKind, TelemetryLevel
from arvis.telemetry.adapters import (
    ERROR_COMPONENT,
    degradation_event,
    error_event,
    escalation_event,
)


def test_escalation_event_carries_counters() -> None:
    stats = {"total": 9, "fatal": 1, "error": 3, "degraded": 2, "fail_closed": 1}
    event = escalation_event(stats)
    assert event.kind is TelemetryKind.ESCALATION
    assert event.level is TelemetryLevel.WARNING
    assert event.component == ERROR_COMPONENT
    assert event.attributes["fatal"] == 1
    assert event.attributes["total"] == 9


def test_degradation_event_maps_state() -> None:
    state = {
        "active": True,
        "count": 4,
        "last_code": "LLM_TIMEOUT",
        "domains": {"llm": 3, "kernel.pipeline": 1},
    }
    event = degradation_event(state)
    assert event.kind is TelemetryKind.DEGRADATION
    assert event.attributes["active"] is True
    assert event.attributes["count"] == 4
    assert event.attributes["last_code"] == "LLM_TIMEOUT"
    assert event.attributes["domains"] == {"llm": 3, "kernel.pipeline": 1}


def test_degradation_event_tolerates_missing_fields() -> None:
    event = degradation_event({})
    assert event.attributes["active"] is False
    assert event.attributes["count"] == 0
    assert event.attributes["last_code"] is None
    assert event.attributes["domains"] == {}


def _error_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "code": "LLM_TIMEOUT",
        "domain": "llm",
        "category": "external",
        "severity": "warning",
        "policy": "degrade",
        "degraded": True,
        "retryable": True,
        "replay_safe": True,
        "sensitive": False,
        "fingerprint": "abc123",
        "created_at": "2026-06-09T00:00:00+00:00",
        "monotonic_ns": 123,
        "error_id": "uuid-xyz",
        "traceback": "secret stack",
    }
    payload.update(overrides)
    return payload


def test_error_event_level_follows_severity() -> None:
    assert error_event(_error_payload(severity="fatal")).level is TelemetryLevel.FATAL
    assert (
        error_event(_error_payload(severity="warning")).level is TelemetryLevel.WARNING
    )
    assert error_event(_error_payload(severity="weird")).level is TelemetryLevel.ERROR


def test_error_event_component_defaults_to_domain() -> None:
    assert error_event(_error_payload()).component == "llm"
    assert error_event(_error_payload(), component="os.api").component == "os.api"


def test_error_event_excludes_nondeterministic_and_sensitive_fields() -> None:
    event = error_event(_error_payload())
    assert event.kind is TelemetryKind.ERROR
    assert event.attributes["code"] == "LLM_TIMEOUT"
    assert event.attributes["error_fingerprint"] == "abc123"
    for forbidden in ("created_at", "monotonic_ns", "error_id", "traceback", "details"):
        assert forbidden not in event.attributes


def test_error_event_threads_replay_and_sensitive_flags() -> None:
    event = error_event(_error_payload(replay_safe=False, sensitive=True))
    assert event.replay_safe is False
    assert event.sensitive is True
