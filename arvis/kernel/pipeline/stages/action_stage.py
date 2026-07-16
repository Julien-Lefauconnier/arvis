# arvis/kernel/pipeline/stages/action_stage.py

from __future__ import annotations

from typing import Any

from arvis.action.action_context import ActionContext
from arvis.action.action_decision import ActionDecision
from arvis.action.action_evaluator import evaluate_action
from arvis.action.action_mode import ActionMode
from arvis.action.action_resolver import resolve_action


class ActionStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        runtime = ctx.execution.execution_state

        can_execute = runtime.can_execute if runtime is not None else False

        requires_confirmation = (
            runtime.requires_confirmation if runtime is not None else False
        )
        # -----------------------------------------
        # RETRY RESOLUTION (EARLY)
        # -----------------------------------------
        runtime_policy = getattr(ctx, "runtime_policy", None)

        # F-001: force_tool is host-injected runtime policy state;
        # the request-facing extra channel never carries it.
        force_tool = runtime_policy.force_tool if runtime_policy is not None else None

        retry_tool_flag = (
            runtime_policy.retry_requested
            if runtime_policy is not None
            else bool(ctx.extra.get("retry_tool", False))
        )

        retry_tool: str | None = None
        retry_payload: dict[str, Any] = {}

        # fallback BEFORE guard
        if retry_tool_flag:
            previous_results = ctx.tooling.tool_results
            if previous_results:
                retry_tool = getattr(previous_results[-1], "tool_name", None)

            payloads = ctx.tooling.tool_payloads
            if payloads:
                retry_payload = payloads[-1].get("payload", {}) or {}

        #  SOURCE OF TRUTH = LOCAL VARIABLE
        resolved_tool = retry_tool or force_tool

        # HARD GUARD
        if not can_execute and not resolved_tool:
            ctx.execution.action_decision = ActionDecision(
                allowed=False,
                requires_user_validation=requires_confirmation,
                denied_reason="execution_blocked",
                audit_required=True,
                action_mode=ActionMode.AUTOMATIC,
            )
            return

        verdict = ctx.gate_result

        if resolved_tool:
            # F-009: forcing a tool selects it; execution authority is
            # never implied. A retry is a re-execution request and keeps
            # executing; a host force_tool executes only if the host
            # explicitly set force_execution=True.
            host_force_execution = (
                runtime_policy.force_execution if runtime_policy is not None else False
            )
            executes = bool(retry_tool) or host_force_execution

            if executes:
                ctx.execution.action_decision = ActionDecision(
                    allowed=True,
                    requires_user_validation=False,
                    denied_reason=None,
                    audit_required=True,
                    action_mode=ActionMode.AUTOMATIC,
                    tool=resolved_tool,
                    tool_payload=retry_payload,
                )
                # lock downstream stages (IntentStage, etc.)
                if runtime_policy is not None:
                    runtime_policy.force_execution = True
                return

            # Selection only: the forced tool is carried on the decision,
            # execution authority stays with the gate verdict.
            ctx.execution.action_decision = ActionDecision(
                allowed=bool(can_execute),
                requires_user_validation=requires_confirmation,
                denied_reason=None if can_execute else "execution_blocked",
                audit_required=True,
                action_mode=ActionMode.AUTOMATIC,
                tool=resolved_tool,
                tool_payload=retry_payload,
            )
            return

        action_template = resolve_action(ctx.decision_layer.decision_result)

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

        action_decision = pipeline.action_policy.apply(
            decision=action_decision,
            risk=ctx.collapse_risk,
        )

        ctx.execution.action_decision = action_decision
