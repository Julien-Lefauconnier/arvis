# arvis/kernel/pipeline/services/pipeline_execution_service.py

from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.kernel.pipeline.cognitive_pipeline_result import (
    CognitivePipelineResult,
)
from arvis.kernel.pipeline.services.pipeline_runner_service import (
    PipelineRunnerService,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
    )
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


class PipelineExecutionService:
    """Execute the full pipeline lifecycle."""

    @staticmethod
    def run(
        pipeline: "CognitivePipeline",
        ctx: "CognitivePipelineContext",
    ) -> CognitivePipelineResult:
        PipelineRunnerService.run_all(pipeline, ctx)

        return pipeline.finalize_run(ctx)
