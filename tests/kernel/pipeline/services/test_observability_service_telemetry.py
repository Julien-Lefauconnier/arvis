# tests/kernel/pipeline/services/test_observability_service_telemetry.py
"""Observability service: canonical tension write, telemetry emission,
and the never-affect-the-run guarantee.

Campaign RELEASE (LOT R2). The service writes the computed tension to
the canonical diagnostics channel (plus the extra export), emits one
telemetry event per present observation, skips absent ones, and a
throwing sink must never affect the run.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.cognition.observability.symbolic.symbolic_drift_snapshot import (
    SymbolicDriftSnapshot,
    SymbolicRegime,
)
from arvis.cognition.observability.symbolic.symbolic_feature_snapshot import (
    SymbolicFeatureSnapshot,
)
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.services.pipeline_observability_service import (
    PipelineObservabilityService,
)
from arvis.math.observability.global_forecast_snapshot import (
    GlobalForecastSnapshot,
)
from arvis.math.observability.multi_horizon_snapshot import MultiHorizonSnapshot
from arvis.math.observability.predictive_snapshot import PredictiveSnapshot
from arvis.math.observability.stability_stats_snapshot import (
    StabilityStatsSnapshot,
)
from arvis.math.signals.system_tension import SystemTensionSignal
from arvis.math.state.symbolic_state import SymbolicState
from arvis.stability.stability_snapshot import StabilitySnapshot
from arvis.telemetry.sink import NullTelemetrySink


class _RecordingSink:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class _BoomSink:
    def emit(self, event: object) -> None:
        raise RuntimeError("sink down")


class _Builder:
    def __init__(self, obs: dict) -> None:
        self._obs = obs

    def build(self, ctx: object) -> dict:
        return dict(self._obs)


class _NoopProjectionStage:
    def refresh(self, pipeline: object, ctx: object) -> None:
        return None


def _pipeline(obs: dict, sink: object) -> SimpleNamespace:
    return SimpleNamespace(
        observability=_Builder(obs),
        projection_stage=_NoopProjectionStage(),
        telemetry_sink=sink,
    )


def _ctx() -> CognitivePipelineContext:
    return CognitivePipelineContext(user_id="test", cognitive_input={})


def _tension() -> SystemTensionSignal:
    return SystemTensionSignal(collapse=0.4, drift=0.1, conflict=0.2)


def _stability() -> StabilitySnapshot:
    return StabilitySnapshot(
        verdict="stable",
        score=0.9,
        confidence=0.8,
        samples=3,
        mean_dv=-0.01,
        std_dv=0.02,
        instability_rate=0.0,
        collapse_risk=0.1,
        last_v=0.2,
        reasons=[],
    )


def _full_obs() -> dict:
    return {
        "system_tension": _tension(),
        "stability": _stability(),
        "predictive": PredictiveSnapshot(
            predicted_v=0.3, slope=0.01, time_to_critical=None, verdict="ALLOW"
        ),
        "multi": MultiHorizonSnapshot(
            collapse_risk=0.1, stability_confidence=0.9, early_warning=False
        ),
        "forecast": GlobalForecastSnapshot(
            predicted_mean_delta=-0.01,
            slope=0.0,
            collapse_risk=0.1,
            time_to_critical=None,
            early_warning=False,
        ),
        "stats": StabilityStatsSnapshot(
            mean_delta=-0.01, contraction_rate=0.9, instability_rate=0.0, samples=3
        ),
        "symbolic_state": SymbolicState(
            intent_type="informational",
            intent_confidence=0.9,
            gate_verdict="ALLOW",
            conversation_mode="default",
            conflict_histogram={},
            conflict_severity=0.0,
            override_count=0,
            override_rate=0.0,
        ),
        "symbolic_drift": SymbolicDriftSnapshot(
            drift_score=0.05,
            regime=SymbolicRegime.OK,
            intent_switch=False,
            gate_switch=False,
            confidence_delta=0.0,
            conflict_delta=0.0,
            override_rate=0.0,
        ),
        "symbolic_features": SymbolicFeatureSnapshot(
            conflict_entropy=0.0,
            contradiction_density=0.0,
            gate_switch_rate=0.0,
            policy_disagreement_rate=0.0,
            symbolic_drift_score=0.05,
            edges_count=0,
            mean_edge_weight=0.0,
            max_edge_weight=0.0,
            spectral_proxy=0.0,
        ),
    }


def test_tension_lands_on_the_canonical_channel_and_the_export() -> None:
    ctx = _ctx()

    PipelineObservabilityService.run(_pipeline(_full_obs(), NullTelemetrySink()), ctx)

    assert ctx.observability.diagnostics.system_tension.collapse == 0.4
    assert ctx.extra["system_tension"] is ctx.observability.diagnostics.system_tension


def test_every_present_observation_emits_one_event() -> None:
    ctx = _ctx()
    sink = _RecordingSink()

    PipelineObservabilityService.run(_pipeline(_full_obs(), sink), ctx)

    # stability + tension + 7 optional observations
    assert len(sink.events) == 9


def test_absent_observations_are_skipped_not_emitted_as_none() -> None:
    ctx = _ctx()
    sink = _RecordingSink()
    obs = {
        "system_tension": _tension(),
        "stability": _stability(),
        "predictive": None,
        "multi": None,
        "forecast": None,
        "stats": None,
        "symbolic_state": None,
        "symbolic_drift": None,
        "symbolic_features": None,
    }

    PipelineObservabilityService.run(_pipeline(obs, sink), ctx)

    assert len(sink.events) == 2  # stability + tension only


def test_a_throwing_sink_never_affects_the_run() -> None:
    ctx = _ctx()

    PipelineObservabilityService.run(_pipeline(_full_obs(), _BoomSink()), ctx)

    # the run continued and the canonical channel is still written
    assert ctx.observability.diagnostics.system_tension is not None


def test_a_throwing_projection_refresh_is_captured_not_raised() -> None:
    ctx = _ctx()
    pipeline = _pipeline(_full_obs(), NullTelemetrySink())

    class _BoomStage:
        def refresh(self, pipeline: object, ctx: object) -> None:
            raise RuntimeError("refresh down")

    pipeline.projection_stage = _BoomStage()

    PipelineObservabilityService.run(pipeline, ctx)

    assert any(
        "Projection refresh" in str(getattr(e, "message", e))
        for e in ctx.error_state.errors
    )


class _FirstBoomSink:
    """Raises on the first emit (the malformed payload), records the
    rest."""

    def __init__(self) -> None:
        self.events: list[object] = []
        self._calls = 0

    def emit(self, event: object) -> None:
        self._calls += 1
        if self._calls == 1:
            raise RuntimeError("malformed payload")
        self.events.append(event)


def test_one_malformed_event_does_not_kill_the_batch() -> None:
    """Campaign FIX (LOT F1, RED-first): one try guarded the whole
    emission block and its except returned, so the first malformed
    payload silently suppressed every following event of the turn.
    Emission must be fail-soft per event: the faulty one is skipped,
    the others still reach the sink."""
    sink = _FirstBoomSink()

    PipelineObservabilityService().run(_pipeline(_full_obs(), sink), _ctx())

    assert len(sink.events) >= 5, len(sink.events)
