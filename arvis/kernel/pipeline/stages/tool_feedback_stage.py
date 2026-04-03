# arvis/kernel/pipeline/stages/tool_feedback_stage.py

from __future__ import annotations

from typing import Any


class ToolFeedbackStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        tool_results = ctx.extra.get("tool_results", [])

        if not tool_results:
            return

        last = tool_results[-1]

        success = last.get("result") is not None

        ctx._tool_success = success
        ctx._tool_failure = not success

        ctx.extra["tool_feedback"] = {
            "tool": last.get("tool"),
            "success": success,
        }