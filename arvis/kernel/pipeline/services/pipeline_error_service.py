from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.errors.manager import ErrorManager
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
        PipelineStage,
    )


class PipelineErrorService:
    @staticmethod
    def safe_stage_run(
        pipeline: CognitivePipeline,
        stage: PipelineStage,
        ctx: CognitivePipelineContext,
    ) -> None:
        try:
            stage.run(pipeline, ctx)

        except Exception as exc:
            ErrorManager.capture_exception(
                ctx=ctx,
                exc=exc,
                code="PIPELINE_STAGE_FAILURE",
                details={
                    "stage": stage.__class__.__name__,
                },
            )
