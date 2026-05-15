from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.errors.base import (
    ArvisInvariantViolation,
    ArvisRuntimeError,
)
from arvis.errors.manager import ErrorManager
from arvis.errors.provenance import cause_from_exception
from arvis.errors.runtime_pipeline import (
    PipelineStageRuntimeError,
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

        except ArvisInvariantViolation:
            raise

        except ArvisRuntimeError as exc:
            ErrorManager.capture_exception(
                ctx=ctx,
                exc=exc,
            )

        except Exception as exc:
            wrapped = PipelineStageRuntimeError(
                message="Unhandled pipeline stage failure",
                details={
                    "stage": stage.__class__.__name__,
                },
                cause=cause_from_exception(exc),
            )

            ErrorManager.capture_exception(
                ctx=ctx,
                exc=wrapped,
                code=wrapped.code,
            )
