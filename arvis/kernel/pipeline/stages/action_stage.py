# arvis/kernel/pipeline/stages/action_stage.py

from __future__ import annotations

from typing import Any

from arvis.action.action_resolver import resolve_action
from arvis.action.action_evaluator import evaluate_action
from arvis.action.action_context import ActionContext


class ActionStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        # 🔥 HARD GUARD (prioritaire)
        if not getattr(ctx, "_can_execute", False):
            from arvis.action.action_decision import ActionDecision
            from arvis.action.action_mode import ActionMode

            ctx.action_decision = ActionDecision(
                allowed=False,
                requires_user_validation=getattr(ctx, "_requires_confirmation", False),
                denied_reason="execution_blocked",
                audit_required=True,
                action_mode=ActionMode.AUTOMATIC,
            )
            return

        # -----------------------------------------
        # NORMAL FLOW
        # -----------------------------------------
        verdict = ctx.gate_result

        action_template = resolve_action(ctx.decision_result)

        action_context = ActionContext(
            user_id=ctx.user_id,
            responsibility_mode=getattr(ctx, "responsibility_mode", "standard"),
        )

        action_decision = evaluate_action(
            verdict=verdict,
            template=action_template,
            risk=ctx.collapse_risk,
            context=action_context,
        )

        action_decision = pipeline.action_policy.apply(
            decision=action_decision,
            risk=ctx.collapse_risk,
        )

        ctx.action_decision = action_decision