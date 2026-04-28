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
        requires_confirmation = ctx._requires_confirmation
        can_execute = ctx._can_execute

        assert ctx.execution_status is not None

        ctx.requires_confirmation = requires_confirmation
        ctx.can_execute = can_execute
