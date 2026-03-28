# arvis/kernel/pipeline/stages/intent_stage.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from arvis.cognition.execution.executable_intent import ExecutableIntent
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class IntentStage:

    def run(self, pipeline: Any, ctx: Any) -> None:
        action_decision = ctx.action_decision
        verdict = getattr(ctx, "gate_result", None)

        print("\n[INTENT DEBUG] START")
        print("[INTENT DEBUG] verdict:", verdict)
        print("[INTENT DEBUG] _can_execute:", getattr(ctx, "_can_execute", None))
        print("[INTENT DEBUG] _requires_confirmation:", getattr(ctx, "_requires_confirmation", None))
        print("[INTENT DEBUG] action_decision:", action_decision)

        if verdict is None:
            ctx.executable_intent = None
            return

        if verdict == LyapunovVerdict.ABSTAIN:
            ctx.executable_intent = None
            return

        ctx.executable_intent = ExecutableIntent(
            bundle_id=str(getattr(ctx.bundle, "bundle_id", "bundle")),
            user_id=ctx.user_id,
            intent_signature=str(getattr(ctx.decision_result, "reason", "opaque")),
            allow_rag=True,
            max_top_k=5,
            provider="default",
            decided_at=datetime.now(timezone.utc),
            linguistic_context=None,
        )

        print("[INTENT DEBUG] exported executable_intent:", ctx.executable_intent)