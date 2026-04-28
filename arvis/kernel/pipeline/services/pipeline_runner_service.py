# arvis/kernel/pipeline/services/pipeline_runner_service.py

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
        PipelineStage,
    )


class PipelineRunnerService:
    @staticmethod
    def run_stage(
        pipeline: "CognitivePipeline",
        ctx: CognitivePipelineContext,
        stage: "PipelineStage",
    ) -> None:
        pipeline._prepare_run(ctx)
        pipeline._safe_run(stage, ctx)

        if stage is pipeline.execution_stage:
            pipeline._sync_execution_flags(ctx)

    @staticmethod
    def run_all(
        pipeline: "CognitivePipeline",
        ctx: CognitivePipelineContext,
    ) -> None:
        pipeline._prepare_run(ctx)

        for stage in pipeline.iter_stages():
            PipelineRunnerService.run_stage(
                pipeline,
                ctx,
                stage,
            )

    @staticmethod
    def run_iter(
        pipeline: "CognitivePipeline",
        ctx: CognitivePipelineContext,
    ) -> Iterator["PipelineStage"]:
        pipeline._prepare_run(ctx)

        for stage in pipeline.iter_stages():
            PipelineRunnerService.run_stage(
                pipeline,
                ctx,
                stage,
            )
            yield stage
