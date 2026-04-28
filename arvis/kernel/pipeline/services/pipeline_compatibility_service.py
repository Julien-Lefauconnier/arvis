# arvis/kernel/pipeline/services/pipeline_compatibility_service.py

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


class PipelineCompatibilityService:
    @staticmethod
    def safe_run(
        pipeline: "CognitivePipeline",
        stage: "PipelineStage",
        ctx: CognitivePipelineContext,
    ) -> None:
        pipeline_error_service = pipeline  # keep pipeline typed context
        pipeline_error_service
        from arvis.kernel.pipeline.services.pipeline_error_service import (
            PipelineErrorService,
        )

        PipelineErrorService.safe_stage_run(
            pipeline,
            stage,
            ctx,
        )

    @staticmethod
    def bootstrap_ir_input(
        ctx: CognitivePipelineContext,
    ) -> None:
        from arvis.kernel.pipeline.services.pipeline_ir_bootstrap_service import (
            PipelineIRBootstrapService,
        )

        PipelineIRBootstrapService.bootstrap_input(ctx)

    @staticmethod
    def bootstrap_ir_context(
        ctx: CognitivePipelineContext,
    ) -> None:
        from arvis.kernel.pipeline.services.pipeline_ir_bootstrap_service import (
            PipelineIRBootstrapService,
        )

        PipelineIRBootstrapService.bootstrap_context(ctx)

    @staticmethod
    def refresh_ir_context_extra(
        ctx: CognitivePipelineContext,
    ) -> None:
        from arvis.kernel.pipeline.services.pipeline_ir_bootstrap_service import (
            PipelineIRBootstrapService,
        )

        PipelineIRBootstrapService.refresh_context_extra(ctx)
