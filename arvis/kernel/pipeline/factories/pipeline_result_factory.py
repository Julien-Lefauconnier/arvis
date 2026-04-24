# arvis/kernel/pipeline/factories/pipeline_result_factory.py

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_result import (
    CognitivePipelineResult,
)
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.execution.execution_gate_status import (
    ExecutionGateStatus,
)

class PipelineResultFactory:

    @staticmethod
    def build(
        ctx: CognitivePipelineContext,
        execution_status: ExecutionGateStatus,
        can_execute: bool,
        requires_confirmation: bool,
    ) -> CognitivePipelineResult:
        return CognitivePipelineResult(
            bundle=ctx.bundle,
            decision=ctx.decision_result,
            scientific=ctx.scientific_snapshot,
            control=ctx.control_snapshot,
            gate_result=ctx.gate_result,
            execution_status=execution_status,
            executable_intent=ctx.executable_intent,
            action_decision=ctx.action_decision,
            confirmation_request=ctx.confirmation_request,
            can_execute=can_execute,
            requires_confirmation=requires_confirmation,
            trace=ctx.trace,
            ir_input=ctx.ir_input,
            ir_context=ctx.ir_context,
            ir_decision=ctx.ir_decision,
            ir_state=ctx.ir_state,
            ir_gate=ctx.ir_gate,
            ir_projection=ctx.ir_projection,
            ir_validity=ctx.ir_validity,
            ir_stability=ctx.ir_stability,
            ir_adaptive=ctx.ir_adaptive,
            cognitive_ir=ctx.cognitive_ir,
            ir_serialized=ctx.ir_serialized,
            ir_hash=ctx.ir_hash,
            ir_envelope=ctx.ir_envelope,
            cognitive_state=ctx.cognitive_state,
        )