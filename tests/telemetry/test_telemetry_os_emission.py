# tests/telemetry/test_telemetry_os_emission.py

from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.stability.stability_snapshot import StabilitySnapshot
from arvis.telemetry import (
    InMemoryTelemetrySink,
    NullTelemetrySink,
    TelemetryKind,
)


def _snapshot() -> StabilitySnapshot:
    return StabilitySnapshot(
        verdict="OK",
        score=0.9,
        confidence=0.8,
        samples=10,
        mean_dv=0.0,
        std_dv=0.0,
        instability_rate=0.0,
        collapse_risk=0.1,
        last_v=0.3,
        reasons=[],
    )


def _view(stability: object) -> CognitiveResultView:
    return CognitiveResultView(
        decision=None,
        stability=stability,
        stability_view=None,
        trace=None,
    )


def test_run_emits_stability_event_to_configured_sink() -> None:
    sink = InMemoryTelemetrySink()
    cog_os = CognitiveOS(CognitiveOSConfig(telemetry_sink=sink))
    cog_os._emit_stability_telemetry(_view(_snapshot()))
    events = sink.events()
    assert len(events) == 1
    assert events[0].kind is TelemetryKind.STABILITY
    assert events[0].attributes["score"] == 0.9
    assert events[0].attributes["collapse_risk"] == 0.1


def test_default_os_uses_null_sink_and_is_noop() -> None:
    cog_os = CognitiveOS()
    assert isinstance(cog_os.telemetry_sink, NullTelemetrySink)
    # NullTelemetrySink by default: must not raise.
    cog_os._emit_stability_telemetry(_view(_snapshot()))


def test_emission_skipped_without_stability_snapshot() -> None:
    sink = InMemoryTelemetrySink()
    cog_os = CognitiveOS(CognitiveOSConfig(telemetry_sink=sink))
    cog_os._emit_stability_telemetry(_view(None))
    assert sink.events() == []
