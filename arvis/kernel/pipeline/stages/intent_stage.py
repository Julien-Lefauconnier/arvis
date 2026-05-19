# arvis/kernel/pipeline/stages/intent_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.execution.executable_intent import ExecutableIntent
from arvis.kernel.pipeline.services.llm_request_builder import LLMRequestBuilder
from arvis.kernel.pipeline.services.pipeline_llm_service import PipelineLLMService
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.types.timestamps import utcnow


class IntentStage:
    def _debug(self, ctx: Any, *parts: object) -> None:
        if not getattr(ctx, "debug", False):
            return

        extra = getattr(ctx, "extra", None)
        if not isinstance(extra, dict):
            return

        extra.setdefault("debug_events", []).append(
            " ".join(str(part) for part in parts)
        )

    def run(self, pipeline: Any, ctx: Any) -> None:
        if getattr(ctx, "_tool_forced_execution", False):
            self._debug(ctx, "[INTENT DEBUG] SKIP (forced tool execution)")

        runtime = getattr(ctx, "execution_state", None)

        can_execute = runtime.can_execute if runtime is not None else False

        requires_confirmation = (
            runtime.requires_confirmation if runtime is not None else False
        )

        action_decision = ctx.execution.action_decision
        verdict = getattr(ctx, "gate_result", None)

        self._debug(ctx, "\n[INTENT DEBUG] START")
        self._debug(ctx, "[INTENT DEBUG] verdict:", verdict)
        self._debug(ctx, "[INTENT DEBUG] can_execute:", can_execute)
        self._debug(
            ctx,
            "[INTENT DEBUG] requires_confirmation:",
            requires_confirmation,
        )
        self._debug(ctx, "[INTENT DEBUG] action_decision:", action_decision)

        if verdict is None:
            ctx.executable_intent = None
            return

        if verdict == LyapunovVerdict.ABSTAIN:
            ctx.executable_intent = None
            return

        ctx.executable_intent = ExecutableIntent(
            bundle_id=str(ctx.decision_layer.bundle_id),
            user_id=ctx.user_id,
            intent_signature=str(
                getattr(
                    ctx.decision_layer.decision_result,
                    "reason",
                    "opaque",
                )
            ),
            allow_rag=True,
            max_top_k=5,
            provider="default",
            decided_at=utcnow(),
            linguistic_context=None,
        )

        self._debug(
            ctx,
            "[INTENT DEBUG] exported executable_intent:",
            ctx.executable_intent,
        )

        request = LLMRequestBuilder.build_intent_enrichment_request(
            ctx,
            ctx.executable_intent,  # ← clean
        )

        content = PipelineLLMService.generate_text(
            ctx,
            request=request,
            stage="IntentStage",
        )

        if content is not None:
            ctx.extra.setdefault("llm", {})["intent_enrichment"] = content
