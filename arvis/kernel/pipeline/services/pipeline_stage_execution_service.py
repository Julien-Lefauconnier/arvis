# arvis/kernel/pipeline/services/pipeline_stage_execution_service.py

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
        PipelineStage,
    )
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


class PipelineStageExecutionService:
    @staticmethod
    def run_stage(
        pipeline: "CognitivePipeline",
        ctx: "CognitivePipelineContext",
        stage: "PipelineStage",
    ) -> None:
        from arvis.kernel.pipeline.services.pipeline_runner_service import (
            PipelineRunnerService,
        )

        PipelineRunnerService.run_stage(
            pipeline,
            ctx,
            stage,
        )