# arvis/kernel/pipeline/services/pipeline_lifecycle_service.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from arvis.ir.cognitive_ir import CognitiveIR
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.cognitive_pipeline_result import (
    CognitivePipelineResult,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
    )


class PipelineLifecycleService:
    @staticmethod
    def run_from_input(
        pipeline: "CognitivePipeline",
        input_data: Dict[str, Any],
    ) -> CognitivePipelineResult:
        from arvis.kernel.pipeline.services.pipeline_input_service import (
            PipelineInputService,
        )

        ctx = PipelineInputService.build_context(
            input_data
        )
        return pipeline.run(ctx)

    @staticmethod
    def finalize(
        pipeline: "CognitivePipeline",
        ctx: CognitivePipelineContext,
    ) -> CognitivePipelineResult:
        from arvis.kernel.pipeline.services.pipeline_finalize_service import (
            PipelineFinalizeService,
        )

        return PipelineFinalizeService.run(
            pipeline,
            ctx,
        )

    @staticmethod
    def run_from_ir(
        pipeline: "CognitivePipeline",
        ir: CognitiveIR,
    ) -> CognitivePipelineResult:
        from arvis.kernel.pipeline.services.pipeline_replay_service import (
            PipelineReplayService,
        )

        ctx = PipelineReplayService.build_context(
            ir
        )
        return pipeline.run(ctx)