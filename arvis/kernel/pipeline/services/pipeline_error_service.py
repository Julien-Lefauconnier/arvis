# arvis/kernel/pipeline/services/pipeline_error_service.py

from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.errors.helpers import append_error
from arvis.errors.pipeline import (
    PipelineStageError,
)
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
            append_error(
                ctx,
                PipelineStageError(
                    message=str(exc),
                    details={
                        "stage": stage.__class__.__name__,
                        "exception_type": type(exc).__name__,
                    },
                ),
            )
