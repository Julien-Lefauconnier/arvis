# arvis/kernel/pipeline/stages/intent_stage.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from arvis.cognition.execution.executable_intent import ExecutableIntent
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.adapters.registry import get_llm_adapter


class IntentStage:

    def run(self, pipeline: Any, ctx: Any) -> None:
        # 🔒 TOOL FORCED EXECUTION LOCK
        if getattr(ctx, "_tool_forced_execution", False):
            print("[INTENT DEBUG] SKIP (forced tool execution)")
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

        # -----------------------------------------------------
        # LLM ENRICHMENT (NON-CRITICAL / SAFE)
        # -----------------------------------------------------
        llm = get_llm_adapter(ctx)

        if llm is not None:
            try:
                prompt = f"""
You are a cognitive assistant inside a Cognitive OS.

Intent:
{ctx.executable_intent}

Provide:
- a short execution plan
- potential risks
- optional refinement

Keep it structured and concise.
"""

                response = llm.generate(
                    prompt,
                    temperature=0.2,
                )

                ctx.extra.setdefault("llm", {})["intent_enrichment"] = response.content

            except Exception as e:
                ctx.extra.setdefault("errors", []).append({
                    "stage": "IntentStage",
                    "llm_error": str(e),
                })