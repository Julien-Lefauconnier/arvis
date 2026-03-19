# arvis/kernel/pipeline/stages/decision_stage.py

from __future__ import annotations

from typing import Any

class DecisionStage:
    """
    Stage 1: decision bootstrap.

    Responsibilities:
    - evaluate the decision layer
    - attach per-user control runtime
    - no side effects outside ctx mutation
    """

    def run(self, pipeline: Any, ctx: Any) -> None:
        decision_result = pipeline.decision.evaluate(ctx)
        ctx.decision_result = decision_result

        # Control Runtime (stateful per user)
        ctx.control_runtime = pipeline._get_control_runtime(ctx.user_id)