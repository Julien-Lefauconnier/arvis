# arvis/kernel/pipeline/services/pipeline_replay_service.py

from __future__ import annotations

from arvis.ir.cognitive_ir import CognitiveIR
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


class PipelineReplayService:
    @staticmethod
    def build_context(
        ir: CognitiveIR,
    ) -> CognitivePipelineContext:
        if ir.context is None:
            raise ValueError("Cannot replay from IR without context")

        if ir.input is None:
            raise ValueError("Cannot replay from IR without input")

        ctx = CognitivePipelineContext(
            user_id=ir.context.user_id,
            cognitive_input=ir.input.metadata,
        )

        ctx.ir_input = ir.input
        ctx.ir_context = ir.context
        ctx.cognitive_ir = ir
        ctx.extra["replay_mode"] = True

        return ctx
