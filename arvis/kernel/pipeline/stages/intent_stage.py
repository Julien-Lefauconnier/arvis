# arvis/kernel/pipeline/stages/intent_stage.py

# =====================================================
# arvis/kernel/pipeline/stages/intent_stage.py
# CLEAN DEBUG-GATED VERSION
# =====================================================

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from arvis.adapters.registry import get_llm_adapter
from arvis.cognition.execution.executable_intent import ExecutableIntent
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class IntentStage:
    def _debug(self, ctx: Any, *parts: object) -> None:
        if getattr(ctx, "debug", False):
            print(*parts)

    def run(self, pipeline: Any, ctx: Any) -> None:
        if getattr(ctx, "_tool_forced_execution", False):
            self._debug(ctx, "[INTENT DEBUG] SKIP (forced tool execution)")

        action_decision = ctx.action_decision
        verdict = getattr(ctx, "gate_result", None)

        self._debug(ctx, "\n[INTENT DEBUG] START")
        self._debug(ctx, "[INTENT DEBUG] verdict:", verdict)
        self._debug(
            ctx, "[INTENT DEBUG] _can_execute:", getattr(ctx, "_can_execute", None)
        )
        self._debug(
            ctx,
            "[INTENT DEBUG] _requires_confirmation:",
            getattr(ctx, "_requires_confirmation", None),
        )
        self._debug(ctx, "[INTENT DEBUG] action_decision:", action_decision)

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
            decided_at=datetime.now(UTC),
            linguistic_context=None,
        )

        self._debug(
            ctx,
            "[INTENT DEBUG] exported executable_intent:",
            ctx.executable_intent,
        )

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
                ctx.extra.setdefault("errors", []).append(
                    {
                        "stage": "IntentStage",
                        "llm_error": str(e),
                    }
                )
