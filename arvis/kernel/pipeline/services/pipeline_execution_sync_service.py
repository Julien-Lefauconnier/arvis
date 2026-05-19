# arvis/kernel/pipeline/services/pipeline_execution_sync_service.py

from __future__ import annotations

from arvis.errors.base import ArvisRuntimeError, ErrorDomain
from arvis.errors.codes import ErrorCode
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


class PipelineExecutionSyncService:
    """
    Legacy compatibility projection layer.

    Runtime execution authority is owned by
    CognitiveExecutionState.

    This service only mirrors runtime-owned state
    into CognitivePipelineContext for backward
    compatibility with older integrations/tests.

    TODO(arvis-runtime-v2):
    remove compatibility projection once all
    consumers migrated to execution_state.
    """

    @staticmethod
    def run(
        ctx: CognitivePipelineContext,
    ) -> None:
        """
        Compatibility hook.

        Execution authority is now runtime-owned and exposed
        through CognitivePipelineContext proxy properties.
        This service remains as a lifecycle hook for older
        pipeline callers but no longer mirrors mutable state.
        """
        runtime = ctx.execution.execution_state

        if runtime is None:
            return

        if runtime.execution_status is None:
            raise ArvisRuntimeError(
                "Pipeline execution sync requires runtime.execution_status",
                code=ErrorCode.PIPELINE_EXECUTION_CONTRACT_VIOLATION,
                domain=ErrorDomain.PIPELINE,
                details={
                    "component": "PipelineExecutionSyncService",
                    "missing": "runtime.execution_status",
                    "retry_class": "permanent",
                },
            )
