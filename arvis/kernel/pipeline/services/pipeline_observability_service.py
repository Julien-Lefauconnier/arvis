# arvis/kernel/pipeline/services/pipeline_observability_service.py

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol, cast

from arvis.errors.boundaries.observability import capture_observability_failure
from arvis.errors.observability import (
    ProjectionRefreshFailure,
    StabilityProjectionFailure,
)
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.stability.stability_state_projector import StabilityStateProjector
from arvis.stability.stability_statistics import (
    StabilityStatistics,
    StabilityStatsSnapshot,
)
from arvis.telemetry.adapters.forecast import forecast_event
from arvis.telemetry.adapters.multi import multi_horizon_event
from arvis.telemetry.adapters.predictive import predictive_event
from arvis.telemetry.adapters.stability import stability_event
from arvis.telemetry.adapters.stats import stats_event
from arvis.telemetry.adapters.symbolic_drift import symbolic_drift_event
from arvis.telemetry.adapters.symbolic_features import symbolic_features_event
from arvis.telemetry.adapters.symbolic_state import symbolic_state_event
from arvis.telemetry.adapters.tension import system_tension_event
from arvis.telemetry.sink import NullTelemetrySink

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline


class RefreshableStage(Protocol):
    def refresh(
        self,
        pipeline: CognitivePipeline,
        ctx: CognitivePipelineContext,
    ) -> None: ...


class PipelineObservabilityService:
    @staticmethod
    def run(
        pipeline: CognitivePipeline,
        ctx: CognitivePipelineContext,
    ) -> None:
        obs = pipeline.observability.build(ctx)

        system_tension = obs.get("system_tension")
        if system_tension is not None:
            ctx.extra["system_tension"] = system_tension
            ctx.observability.diagnostics.system_tension = system_tension

        try:
            projection_stage = cast(
                RefreshableStage,
                pipeline.projection_stage,
            )
            projection_stage.refresh(pipeline, ctx)

        except Exception as exc:
            capture_observability_failure(
                ctx,
                exc,
                error_cls=ProjectionRefreshFailure,
                message="Projection refresh failed",
                component="PipelineObservabilityService.projection_refresh",
            )

        projections = ctx.observability.projections
        projections.predictive_snapshot = obs["predictive"]
        projections.multi_horizon = obs["multi"]
        projections.global_forecast = obs["forecast"]
        projections.global_stability = obs["stability"]
        projections.stability_stats = obs["stats"]

        ctx.scientific.lyapunov.symbolic_state = obs["symbolic_state"]
        ctx.observability.symbolic.symbolic_drift = obs["symbolic_drift"]
        ctx.observability.symbolic.symbolic_features = obs["symbolic_features"]

        try:
            projector = StabilityStateProjector()
            stats = StabilityStatistics()

            projected = projector.project(projections.global_stability)
            computed = stats.compute(cast(StabilityStatsSnapshot, projected))

            projections.stability_projection = projected
            projections.stability_statistics = computed

        except Exception as exc:
            projections.stability_projection = None
            projections.stability_statistics = None
            capture_observability_failure(
                ctx,
                exc,
                error_cls=StabilityProjectionFailure,
                message="Stability projection failed",
                component="PipelineObservabilityService.stability_projection",
            )

        # Surface the rich stability snapshot via telemetry (observe-only,
        # fail-safe; NullTelemetrySink is a no-op). obs["stability"] is the
        # full StabilitySnapshot, the authoritative stability source.
        # Fail-soft PER EVENT (campaign FIX, LOT F1): one shared try
        # used to return on the first exception, so a single malformed
        # payload silently suppressed every following event of the
        # turn. A faulty event is skipped; the others still emit; the
        # run is never affected either way.
        sink = pipeline.telemetry_sink
        if not isinstance(sink, NullTelemetrySink):
            adapters: tuple[tuple[str, Callable[[Any], Any]], ...] = (
                ("stability", stability_event),
                ("system_tension", system_tension_event),
                ("predictive", predictive_event),
                ("multi", multi_horizon_event),
                ("forecast", forecast_event),
                ("stats", stats_event),
                ("symbolic_state", symbolic_state_event),
                ("symbolic_drift", symbolic_drift_event),
                ("symbolic_features", symbolic_features_event),
            )
            for key, adapt in adapters:
                value = obs.get(key)
                if value is None:
                    continue
                try:
                    sink.emit(adapt(value))
                except Exception:  # arvis-broad: telemetry never affects a run
                    continue
