# arvis/kernel/pipeline/services/pipeline_error_service.py

from __future__ import annotations

from typing import TYPE_CHECKING

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
        except Exception as e:
            ctx.extra.setdefault("errors", []).append(
                {
                    "stage": stage.__class__.__name__,
                    "error": str(e),
                    "type": type(e).__name__,
                }
            )
