# arvis/kernel/pipeline/stages/action_stage.py

from __future__ import annotations

from typing import Any

from arvis.action.action_resolver import resolve_action
from arvis.action.action_evaluator import evaluate_action
from arvis.action.action_context import ActionContext


class ActionStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        verdict = ctx.gate_result

        # -----------------------------------------
        # 1. RESOLVE TEMPLATE
        # -----------------------------------------
        action_template = resolve_action(ctx.decision_result)

        # -----------------------------------------
        # 2. BUILD CONTEXT
        # -----------------------------------------
        action_context = ActionContext(
            user_id=ctx.user_id,
            responsibility_mode=getattr(ctx, "responsibility_mode", "standard"),
        )

        # -----------------------------------------
        # 3. EVALUATE
        # -----------------------------------------
        action_decision = evaluate_action(
            verdict=verdict,
            template=action_template,
            risk=ctx.collapse_risk,
            context=action_context,
        )

        # -----------------------------------------
        # 4. POLICY LAYER
        # -----------------------------------------
        action_decision = pipeline.action_policy.apply(
            decision=action_decision,
            risk=ctx.collapse_risk,
        )

        # -----------------------------------------
        # 5. EXPORT
        # -----------------------------------------
        ctx.action_decision = action_decision