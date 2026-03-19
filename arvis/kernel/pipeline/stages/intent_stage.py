# arvis/kernel/pipeline/stages/intent_stage.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from arvis.cognition.execution.executable_intent import ExecutableIntent


class IntentStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        action_decision = ctx.action_decision

        executable_intent = None

        if action_decision and action_decision.allowed:
            executable_intent = ExecutableIntent(
                bundle_id=str(getattr(ctx.bundle, "bundle_id", "bundle")),
                user_id=ctx.user_id,
                intent_signature=str(getattr(ctx.decision_result, "reason", "opaque")),
                allow_rag=True,
                max_top_k=5,
                provider="default",
                decided_at=datetime.now(timezone.utc),
                linguistic_context=None,
            )

        ctx.executable_intent = executable_intent