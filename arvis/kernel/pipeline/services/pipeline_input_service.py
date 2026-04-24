# arvis/kernel/pipeline/services/pipeline_input_service.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)

from arvis.kernel.pipeline.services.pipeline_ir_bootstrap_service import (
    PipelineIRBootstrapService,
)


class PipelineInputService:
    @staticmethod
    def build_context(
        input_data: dict[str, Any],
    ) -> CognitivePipelineContext:

        ctx = CognitivePipelineContext(
            user_id=input_data.get(
                "user_id",
                "anonymous",
            ),
            cognitive_input=input_data.get(
                "cognitive_input",
                {},
            ),
            long_memory=input_data.get(
                "long_memory",
                {},
            ) or {},
            timeline=input_data.get(
                "timeline",
                [],
            ) or [],
            introspection=input_data.get(
                "introspection"
            ),
        )

        ctx.extra = getattr(ctx, "extra", {})
        ctx.extra["input_data"] = input_data

        if "session_id" in input_data:
            ctx.extra["session_id"] = input_data["session_id"]

        if "conversation_mode" in input_data:
            ctx.extra["conversation_mode"] = input_data["conversation_mode"]

        PipelineIRBootstrapService.bootstrap_input(ctx)
        PipelineIRBootstrapService.bootstrap_context(ctx)

        return ctx