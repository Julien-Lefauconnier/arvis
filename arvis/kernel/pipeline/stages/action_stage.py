# arvis/kernel/pipeline/stages/action_stage.py

from __future__ import annotations

from typing import Any
from dataclasses import replace

from arvis.action.action_resolver import resolve_action
from arvis.action.action_evaluator import evaluate_action
from arvis.action.action_context import ActionContext
from arvis.action.action_decision import ActionDecision
from arvis.action.action_mode import ActionMode


class ActionStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        # -----------------------------------------
        # RETRY RESOLUTION (EARLY)
        # -----------------------------------------
        force_tool = ctx.extra.get("force_tool")
        retry_tool_flag = ctx.extra.get("execution_policy", {}).get(
            "retry"
        ) or ctx.extra.get("retry_tool")

        retry_tool = getattr(ctx.decision_result, "tool", None)

        # fallback BEFORE guard
        if retry_tool_flag and not retry_tool:
            previous_results = ctx.extra.get("tool_results", [])
            if previous_results:
                retry_tool = getattr(previous_results[-1], "tool_name", None)
        # 🔥 SOURCE OF TRUTH = LOCAL VARIABLE
        resolved_tool = retry_tool or force_tool

        # HARD GUARD
        if not getattr(ctx, "_can_execute", False) and not resolved_tool:
            ctx.action_decision = ActionDecision(
                allowed=False,
                requires_user_validation=getattr(ctx, "_requires_confirmation", False),
                denied_reason="execution_blocked",
                audit_required=True,
                action_mode=ActionMode.AUTOMATIC,
            )
            return

        verdict = ctx.gate_result
        retry_tool = getattr(ctx.decision_result, "tool", None)

        if resolved_tool:
            ctx.action_decision = ActionDecision(
                allowed=True,
                requires_user_validation=False,
                denied_reason=None,
                audit_required=True,
                action_mode=ActionMode.AUTOMATIC,
                tool=resolved_tool,
                tool_payload=getattr(ctx.decision_result, "tool_payload", {}) or {},
            )
            # lock downstream stages (IntentStage, etc.)
            ctx._tool_forced_execution = True

            return

        action_template = resolve_action(ctx.decision_result)

        # 🔒 fallback if no template
        if action_template is None:
            action_template = {}

        action_context = ActionContext(
            user_id=ctx.user_id,
            responsibility_mode=getattr(ctx, "responsibility_mode", "standard"),
        )

        # -----------------------------------------
        # FORCE TOOL EXECUTION (pre-evaluation override)
        # -----------------------------------------

        if force_tool:
            setattr(ctx.decision_result, "tool", force_tool)

        # optional sync (not required anymore)
        if resolved_tool:
            setattr(ctx.decision_result, "tool", resolved_tool)

        action_decision = evaluate_action(
            verdict=verdict,
            template=action_template,
            risk=ctx.collapse_risk,
            context=action_context,
        )
        if action_decision is None:
            action_decision = ActionDecision(
                allowed=False,
                requires_user_validation=False,
                denied_reason="no_action_template",
                audit_required=True,
                action_mode=ActionMode.MANUAL,
            )

        if resolved_tool:
            action_decision = replace(
                action_decision,
                allowed=True,
                tool=resolved_tool,
                tool_payload=getattr(ctx.decision_result, "tool_payload", {}) or {},
            )

        # -----------------------------------------
        # TOOL RETRY OVERRIDE
        # -----------------------------------------
        retry_tool = getattr(ctx.decision_result, "tool", None)

        if retry_tool:
            action_decision = replace(
                action_decision,
                allowed=True,
                tool=retry_tool,
                tool_payload=getattr(ctx.decision_result, "tool_payload", {}) or {},
            )

        tool_name = None
        tool_payload = None

        decision_result = getattr(ctx, "decision_result", None)
        if decision_result is not None:
            tool_name = getattr(decision_result, "tool", None)
            tool_payload = getattr(decision_result, "tool_payload", None)

        if tool_name and getattr(action_decision, "allowed", False):
            action_decision = replace(
                action_decision,
                tool=tool_name,
                tool_payload=tool_payload or {},
            )

        action_decision = pipeline.action_policy.apply(
            decision=action_decision,
            risk=ctx.collapse_risk,
        )

        ctx.action_decision = action_decision
