# arvis/kernel/pipeline/stages/tool_retry_stage.py

from typing import Any

from arvis.tools.retry_policy import ToolRetryPolicy


class ToolRetryStage:
    def __init__(self) -> None:
        self.policy = ToolRetryPolicy()

    def run(self, pipeline: Any, ctx: Any) -> None:
        self.policy.evaluate(ctx)
