# arvis/kernel/pipeline/services/pipeline_runner_service.py

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
        PipelineStage,
    )


class PipelineRunnerService:
    """
    Runtime pipeline stage orchestrator.

    Lifecycle preparation is performed once at the
    pipeline execution boundary.

    Individual stage execution MUST remain side-effect
    free regarding runtime bootstrap/preparation.
    """

    @staticmethod
    def run_stage(
        pipeline: CognitivePipeline,
        ctx: CognitivePipelineContext,
        stage: PipelineStage,
    ) -> None:
        pipeline._safe_run(stage, ctx)

        # -----------------------------------------
        # Legacy compatibility projection
        # -----------------------------------------
        if stage is pipeline.execution_stage:
            pipeline._sync_execution_flags(ctx)

    @staticmethod
    def run_all(
        pipeline: CognitivePipeline,
        ctx: CognitivePipelineContext,
    ) -> None:
        # -----------------------------------------
        # Single lifecycle preparation point
        # -----------------------------------------
        pipeline._prepare_run(ctx)

        for stage in pipeline.iter_stages():
            PipelineRunnerService.run_stage(
                pipeline,
                ctx,
                stage,
            )

    @staticmethod
    def run_iter(
        pipeline: CognitivePipeline,
        ctx: CognitivePipelineContext,
    ) -> Iterator[PipelineStage]:
        # -----------------------------------------
        # Single lifecycle preparation point
        # -----------------------------------------
        pipeline._prepare_run(ctx)

        for stage in pipeline.iter_stages():
            PipelineRunnerService.run_stage(
                pipeline,
                ctx,
                stage,
            )

            yield stage
