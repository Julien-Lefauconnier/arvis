# arvis/kernel/pipeline/services/pipeline_observability_service.py

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

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
from arvis.telemetry.adapters.stability import stability_event
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

        ctx.predictive_snapshot = obs["predictive"]
        ctx.multi_horizon = obs["multi"]
        ctx.global_forecast = obs["forecast"]
        ctx.global_stability = obs["stability"]
        ctx.stability_stats = obs["stats"]

        ctx.symbolic_state = obs["symbolic_state"]
        ctx.symbolic_drift = obs["symbolic_drift"]
        ctx.symbolic_features = obs["symbolic_features"]

        try:
            projector = StabilityStateProjector()
            stats = StabilityStatistics()

            projected = projector.project(ctx.global_stability)
            computed = stats.compute(cast(StabilityStatsSnapshot, projected))

            ctx.stability_projection = projected
            ctx.stability_statistics = computed

        except Exception as exc:
            ctx.stability_projection = None
            ctx.stability_statistics = None
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
        sink = pipeline.telemetry_sink
        if not isinstance(sink, NullTelemetrySink):
            try:
                sink.emit(stability_event(obs["stability"]))
            except Exception:
                # Telemetry must never affect a run.
                return
