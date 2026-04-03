# arvis/kernel/pipeline/stages/decision_stage.py

from __future__ import annotations

from dataclasses import replace
from typing import Any
from arvis.adapters.ir.decision_adapter import DecisionIRAdapter

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
        # -----------------------------------------
        # TOOL RETRY INJECTION (post-decision override)
        # -----------------------------------------
        if ctx.extra.get("retry_tool"):

            previous_results = ctx.extra.get("tool_results", [])
            if previous_results:
                last = previous_results[-1]
                last_tool = getattr(last, "tool_name", None)

                if last_tool:
                    payloads = ctx.extra.get("tool_payloads", [])
                    last_payload = payloads[-1]["payload"] if payloads else {}

                    ctx.decision_result = replace(
                        ctx.decision_result,
                        tool=last_tool,
                        tool_payload=last_payload,
                    )
        try:
            ctx.ir_decision = DecisionIRAdapter.from_result(decision_result)
        except Exception:
            ctx.extra.setdefault("errors", []).append("decision_ir_adapter_failure")

        # Control Runtime (stateful per user)
        ctx.control_runtime = pipeline._get_control_runtime(ctx.user_id)