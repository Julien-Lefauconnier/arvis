# arvis/kernel/pipeline/services/pipeline_iteration_service.py

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
        PipelineStage,
    )
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


class PipelineIterationService:
    @staticmethod
    def run_iter(
        pipeline: "CognitivePipeline",
        ctx: "CognitivePipelineContext",
    ) -> Iterator["PipelineStage"]:
        from arvis.kernel.pipeline.services.pipeline_runner_service import (
            PipelineRunnerService,
        )

        yield from PipelineRunnerService.run_iter(
            pipeline,
            ctx,
        )