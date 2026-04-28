# arvis/kernel/pipeline/stages/decision_stage.py

from __future__ import annotations

from dataclasses import replace
from typing import Any
from arvis.adapters.ir.decision_adapter import DecisionIRAdapter
from arvis.cognition.decision.decision_result import DecisionResult


class DecisionStage:
    """
    Stage 1: decision bootstrap.

    Responsibilities:
    - evaluate the decision layer
    - attach per-user control runtime
    - no side effects outside ctx mutation
    """

    def run(self, pipeline: Any, ctx: Any) -> None:
        raw_result = pipeline.decision.evaluate(ctx)

        # -----------------------------------------------------
        # Normalize → always DecisionResult (ZK-safe)
        # -----------------------------------------------------
        if isinstance(raw_result, DecisionResult):
            decision_result = raw_result
        else:
            # backward compatibility (SimpleNamespace / dict / etc.)
            decision_result = DecisionResult(
                reason=getattr(raw_result, "reason", "unknown"),
            )

        # -----------------------------------------------------
        # Ensure memory_influence is always present (ZK-safe)
        # -----------------------------------------------------
        if not hasattr(decision_result, "memory_influence"):
            decision_result = replace(decision_result, memory_influence={})

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

                    ctx.extra["tool_override"] = {
                        "tool": last_tool,
                        "payload": last_payload,
                    }

        try:
            ctx.ir_decision = DecisionIRAdapter.from_result(ctx.decision_result)
        except Exception:
            ctx.extra.setdefault("errors", []).append("decision_ir_adapter_failure")

        # Control Runtime (stateful per user)
        ctx.control_runtime = pipeline._get_control_runtime(ctx.user_id)
