# arvis/kernel/pipeline/stages/decision_stage.py

from __future__ import annotations

from dataclasses import replace
from typing import Any

from arvis.adapters.ir.decision_adapter import DecisionIRAdapter
from arvis.cognition.decision.decision_result import DecisionResult
from arvis.errors.boundaries.pipeline import (
    capture_pipeline_degraded_failure,
)


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

        ctx.decision_layer.decision_result = decision_result
        # -----------------------------------------
        # TOOL RETRY INJECTION (post-decision override)
        # -----------------------------------------
        runtime_policy = getattr(ctx, "runtime_policy", None)
        retry_requested = (
            runtime_policy.retry_requested if runtime_policy is not None else False
        )

        if retry_requested:
            previous_results = ctx.tooling.tool_results
            if previous_results:
                last = previous_results[-1]
                last_tool = getattr(last, "tool_name", None)

                if last_tool:
                    payloads = ctx.tooling.tool_payloads
                    last_payload = payloads[-1]["payload"] if payloads else {}

                    ctx.tooling.tool_feedback = {
                        "tool_override": {
                            "tool": last_tool,
                            "payload": last_payload,
                        }
                    }

        try:
            ctx.decision_layer.ir_decision = DecisionIRAdapter.from_result(
                ctx.decision_layer.decision_result,
            )
        except Exception as exc:
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="DecisionIRAdapter",
                message="Decision IR adapter failure",
            )

        # Control Runtime (stateful per user)
        ctx.runtime_bindings.control_runtime = pipeline._get_control_runtime(
            ctx.user_id
        )
