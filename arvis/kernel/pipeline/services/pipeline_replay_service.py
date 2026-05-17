# arvis/kernel/pipeline/services/pipeline_replay_service.py

from __future__ import annotations

from dataclasses import is_dataclass

from arvis.ir.cognitive_ir import CognitiveIR
from arvis.ir.context import CognitiveContextIR
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


class PipelineReplayService:
    @staticmethod
    def build_context(
        ir: CognitiveIR,
    ) -> CognitivePipelineContext:
        if ir.input is None:
            raise ValueError("Cannot replay from IR without input")

        ir_context = ir.context

        if ir_context is None:
            raise ValueError("Cannot replay from IR without context")

        if isinstance(ir_context, type):
            ir_context = CognitiveContextIR(
                user_id=str(ir.input.actor_id),
                session_id=None,
                conversation_mode=None,
                long_memory_constraints=(),
                long_memory_preferences={},
                memory_present=False,
                memory_pressure=0.0,
                memory_has_constraints=False,
                memory_constraint_count=0,
                memory_has_language_pref=False,
                memory_has_timezone=False,
                extra={
                    "memory_pressure": 0.0,
                    "has_constraints": False,
                    "has_timezone": False,
                    "has_language_pref": False,
                    "replay_context_rebuilt": True,
                },
            )

        if not is_dataclass(ir_context):
            raise TypeError("IR replay context must be a dataclass instance")

        ctx = CognitivePipelineContext(
            user_id=ir_context.user_id,
            cognitive_input=ir.input.metadata,
        )

        ctx.ir_input = ir.input
        ctx.ir_context = ir_context
        ctx.cognitive_ir = ir
        ctx.extra["replay_mode"] = True

        return ctx
