# arvis/kernel/pipeline/stages/tool_feedback_stage.py

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


class ToolFeedbackStage:
    def run(self, pipeline: CognitivePipeline, ctx: CognitivePipelineContext) -> None:
        tool_results = ctx.extra.get("tool_results", [])

        if not tool_results:
            return

        last = tool_results[-1]

        success = last.get("result") is not None

        ctx.tooling.tool_success = success
        ctx.tooling.tool_failure = not success

        ctx.extra["tool_feedback"] = {
            "tool": last.get("tool"),
            "success": success,
        }
