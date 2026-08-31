# arvis/kernel/pipeline/stages/tool_retry_stage.py

from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.tools.retry_policy import ToolRetryPolicy

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


class ToolRetryStage:
    def __init__(self) -> None:
        self.policy = ToolRetryPolicy()

    def run(self, pipeline: CognitivePipeline, ctx: CognitivePipelineContext) -> None:
        self.policy.evaluate(ctx)
