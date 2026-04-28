# arvis/kernel/pipeline/services/pipeline_observability_service.py

from __future__ import annotations

from typing import TYPE_CHECKING, cast, Protocol

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)

from arvis.stability.stability_state_projector import StabilityStateProjector
from arvis.stability.stability_statistics import (
    StabilityStatistics,
    StabilityStatsSnapshot,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline


class RefreshableStage(Protocol):
    def refresh(
        self,
        pipeline: "CognitivePipeline",
        ctx: CognitivePipelineContext,
    ) -> None: ...


class PipelineObservabilityService:
    @staticmethod
    def run(
        pipeline: "CognitivePipeline",
        ctx: CognitivePipelineContext,
    ) -> None:
        obs = pipeline.observability.build(ctx)

        system_tension = obs.get("system_tension")
        if system_tension is not None:
            ctx.extra["system_tension"] = system_tension
            ctx.system_tension = system_tension

        try:
            projection_stage = cast(
                RefreshableStage,
                pipeline.projection_stage,
            )
            projection_stage.refresh(pipeline, ctx)
        except Exception:
            ctx.extra.setdefault("errors", []).append("projection_refresh_failure")

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

        except Exception:
            ctx.stability_projection = None
            ctx.stability_statistics = None
