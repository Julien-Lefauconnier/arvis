# arvis/kernel/pipeline/services/pipeline_finalize_service.py

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, cast

from arvis.adapters.ir.gate_adapter import GateIRAdapter
from arvis.adapters.ir.state_adapter import StateIRAdapter
from arvis.cognition.gate.cognitive_gate_result import CognitiveGateResult
from arvis.cognition.gate.gate_trace_builder import GateTraceBuilder
from arvis.cognition.gate.reason_code_normalizer import ReasonCodeNormalizer
from arvis.cognition.state.cognitive_state_builder import CognitiveStateBuilder
from arvis.errors.manager import ErrorManager
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.cognitive_pipeline_result import CognitivePipelineResult
from arvis.kernel.pipeline.factories import (
    PipelineResultFactory,
    PipelineTraceFactory,
)
from arvis.kernel.pipeline.services.pipeline_ir_service import (
    PipelineIRService,
)
from arvis.kernel.pipeline.services.pipeline_observability_service import (
    PipelineObservabilityService,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline


class PipelineFinalizeService:
    @staticmethod
    def run(
        pipeline: CognitivePipeline,
        ctx: CognitivePipelineContext,
    ) -> CognitivePipelineResult:
        if ctx.extra.get("__pipeline_finalized", False):
            cached = ctx.extra.get("__pipeline_result")
            if cached is not None:
                return cast(CognitivePipelineResult, cached)

        # -----------------------------------------------------
        # Runtime-owned execution authority
        # -----------------------------------------------------
        runtime = ctx.execution_state

        assert runtime is not None
        assert runtime.execution_status is not None

        requires_confirmation = runtime.requires_confirmation
        can_execute = runtime.can_execute
        execution_status = runtime.execution_status

        # -----------------------------------------------------
        # Public compatibility mirror
        # -----------------------------------------------------
        ctx.requires_confirmation = requires_confirmation

        # -----------------------------------------------------
        # OBSERVABILITY
        # -----------------------------------------------------
        PipelineObservabilityService.run(pipeline, ctx)

        # -----------------------------------------------------
        # DECISION TRACE
        # -----------------------------------------------------
        if ctx.gate_result is None:
            warnings.warn(
                "gate_result is None → fallback ABSTAIN (verify gate_stage)",
                RuntimeWarning,
                stacklevel=2,
            )
            ctx.gate_result = LyapunovVerdict.ABSTAIN

        gate_decision_trace = GateTraceBuilder.build(
            tuple(ctx.extra.get("verdict_transition_trace", []) or ())
        )

        raw_reason_codes = ctx.extra.get("final_reason_codes", ()) or ()
        final_reason_codes = ReasonCodeNormalizer.normalize(raw_reason_codes)

        if isinstance(ctx.gate_result, LyapunovVerdict):
            normalized_gate_result = CognitiveGateResult.from_lyapunov(
                ctx.gate_result,
                bundle_id=str(
                    getattr(ctx.decision_layer.bundle, "bundle_id", "bundle")
                ),
                reason_codes=final_reason_codes,
                decision_trace=gate_decision_trace,
            )
        else:
            normalized_gate_result = CognitiveGateResult.from_lyapunov(
                LyapunovVerdict.ABSTAIN,
                bundle_id=str(
                    getattr(ctx.decision_layer.bundle, "bundle_id", "bundle")
                ),
                reason_codes=final_reason_codes or ("fallback_abstain",),
                decision_trace=gate_decision_trace,
            )

        try:
            ctx.ir_gate = GateIRAdapter.from_gate(normalized_gate_result)
        except Exception as exc:
            ErrorManager.capture_exception(
                ctx=ctx,
                exc=exc,
                code="GATE_IR_ADAPTER_FAILURE",
                details={
                    "component": "GateIRAdapter",
                },
            )
            ctx.ir_gate = None

        # -----------------------------------------------------
        # COGNITIVE IR lifecycle
        # -----------------------------------------------------
        try:
            pipeline._refresh_ir_context_extra(ctx)
        except Exception as exc:
            ErrorManager.capture_exception(
                ctx=ctx,
                exc=exc,
                code="IR_CONTEXT_REFRESH_FAILURE",
                details={
                    "component": "PipelineIRContextRefresh",
                },
            )
        PipelineIRService.run(ctx)

        # -----------------------------------------------------
        # TRACE
        # -----------------------------------------------------
        trace = PipelineTraceFactory.build(
            ctx,
            normalized_gate_result,
        )
        ctx.trace = trace

        # -----------------------------------------------------
        # COGNITIVE STATE
        # -----------------------------------------------------
        try:
            ctx.cognitive_state = CognitiveStateBuilder.from_context(ctx)
        except Exception as exc:
            ctx.cognitive_state = None

            ErrorManager.capture_exception(
                ctx=ctx,
                exc=exc,
                code="COGNITIVE_STATE_BUILD_FAILURE",
                details={
                    "component": "CognitiveStateBuilder",
                },
            )

        # -----------------------------------------------------
        # CONTRACT VALIDATION
        # -----------------------------------------------------
        try:
            if ctx.cognitive_state is not None:
                from arvis.contracts.cognitive_state_contract import (
                    CognitiveStateContract,
                )

                CognitiveStateContract.validate(ctx.cognitive_state)
        except Exception as exc:
            ErrorManager.capture_exception(
                ctx=ctx,
                exc=exc,
                code="COGNITIVE_STATE_CONTRACT_FAILURE",
                details={
                    "component": "CognitiveStateContract",
                },
            )

            ctx.cognitive_state = None

        # -----------------------------------------------------
        # STATE IR
        # -----------------------------------------------------
        try:
            if ctx.cognitive_state is not None:
                ctx.ir_state = StateIRAdapter.from_state(ctx.cognitive_state)
            else:
                ctx.ir_state = None
        except Exception as exc:
            ErrorManager.capture_exception(
                ctx=ctx,
                exc=exc,
                code="STATE_IR_ADAPTER_FAILURE",
                details={
                    "component": "StateIRAdapter",
                },
            )

            ctx.ir_state = None

        # -----------------------------------------------------
        # Sync canonical projections
        # -----------------------------------------------------
        ctx.can_execute = can_execute
        ctx.execution_status = execution_status
        ctx.control = ctx.control_snapshot

        result = PipelineResultFactory.build(
            ctx,
            execution_status=execution_status,
            can_execute=can_execute,
            requires_confirmation=requires_confirmation,
        )

        ctx.extra["__pipeline_finalized"] = True
        ctx.extra["__pipeline_result"] = result

        return result
