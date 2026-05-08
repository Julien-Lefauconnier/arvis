# arvis/kernel/pipeline/services/pipeline_execution_sync_service.py

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


class PipelineExecutionSyncService:
    @staticmethod
    def run(
        ctx: CognitivePipelineContext,
    ) -> None:
        runtime = ctx.execution_state

        requires_confirmation = (
            runtime.requires_confirmation
            if runtime is not None
            else ctx._requires_confirmation
        )

        can_execute = runtime.can_execute if runtime is not None else ctx._can_execute

        assert ctx.execution_status is not None

        # -------------------------------------------------
        # Legacy compatibility mirror
        # TODO(arvis-runtime-v2):
        # remove mutable execution authority from
        # CognitivePipelineContext once all runtime
        # consumers migrated to CognitiveExecutionState.
        # -------------------------------------------------

        ctx.requires_confirmation = requires_confirmation
        ctx.can_execute = can_execute
