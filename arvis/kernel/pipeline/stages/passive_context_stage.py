# arvis/kernel/pipeline/stages/passive_context_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.conversation.conversation_signal import ConversationSignal
from arvis.cognition.coherence.change_budget import ChangeBudget


class PassiveContextStage:
    """
    Stage 2: passive context enrichment.

    Responsibilities:
    - governance (best effort)
    - pending actions (placeholder)
    - events (placeholder)
    - coherence policy projection
    - conversation signal projection

    Pure ctx mutation, no hard dependency guarantees.
    """

    def run(self, pipeline: Any, ctx: Any) -> None:

        # ensure extra dict exists
        if not hasattr(ctx, "extra") or ctx.extra is None:
            ctx.extra = {}

        # -----------------------------------------------------
        # MEMORY INJECTION (PASSIVE, KERNEL-COMPAT)
        # -----------------------------------------------------
        try:
            # Case 1 — snapshot déjà injecté (preferred path)
            snapshot = getattr(ctx, "memory_snapshot", None)

            # Case 2 — projection déjà fournie (external injection)
            projection = getattr(ctx, "memory_projection", None)

            # Case 3 — fallback legacy (long_memory)
            if snapshot is None and projection is None:
                legacy = getattr(ctx, "long_memory", None)
                if isinstance(legacy, dict) and legacy:
                    ctx.memory_projection = legacy
                    projection = legacy

            # Normalize projection for downstream stages
            if projection is not None:
                ctx.memory_projection = projection

                # Optional: keep legacy compatibility
                if not getattr(ctx, "long_memory", None):
                    ctx.long_memory = projection

            # Snapshot always wins over projection
            if snapshot is not None:
                ctx.memory_snapshot = snapshot

        except Exception:
            ctx.extra.setdefault("errors", []).append("memory_injection_failure")

        # -----------------------------------------------------
        # GOVERNANCE (PASSIVE)
        # -----------------------------------------------------
        try:
            if hasattr(pipeline, "governance"):
                ctx.governance = pipeline.governance.evaluate(ctx.decision_result)
            else:
                ctx.governance = None
        except Exception:
            ctx.governance = None

        # -----------------------------------------------------
        # PENDING (PASSIVE)
        # -----------------------------------------------------
        try:
            ctx.pending_actions = []
        except Exception:
            ctx.pending_actions = None

        # -----------------------------------------------------
        # EVENTS (PASSIVE)
        # -----------------------------------------------------
        try:
            ctx.events = []
        except Exception:
            ctx.events = None

        # -----------------------------------------------------
        # COHERENCE POLICY (PASSIVE)
        # -----------------------------------------------------
        try:
            coherence_snapshot = None
            if hasattr(pipeline, "coherence_observer"):
                coherence_snapshot = pipeline.coherence_observer.observe(ctx)

            budget = ChangeBudget(
                current_changes=int(getattr(coherence_snapshot, "change_count", 0)),
                max_changes=int(getattr(coherence_snapshot, "max_change_budget", 0)),
                timestamp=0,
            )

            result = None
            if hasattr(pipeline, "coherence_policy"):
                result = pipeline.coherence_policy.evaluate(
                    snapshot=coherence_snapshot,
                    budget=budget,
                )

            ctx.coherence_policy = [result] if result else []

        except Exception:
            ctx.coherence_policy = None

        # -----------------------------------------------------
        # CONVERSATION PROJECTION (PASSIVE)
        # -----------------------------------------------------
        if getattr(ctx, "conversation_context", None) is not None:
            state = getattr(ctx.conversation_context, "state", None)

            ctx.conversation_signal = ConversationSignal(
                strategy=ctx.conversation_context.proposed_strategy,
                turn_count=int(getattr(state, "turn_count", 0) or 0),
                momentum=float(getattr(state, "momentum", 0.0) or 0.0),
            )

            # expose minimal info to pipeline without coupling
            ctx.extra["conversation_turn"] = ctx.conversation_signal.turn_count
            ctx.extra["conversation_momentum"] = ctx.conversation_signal.momentum