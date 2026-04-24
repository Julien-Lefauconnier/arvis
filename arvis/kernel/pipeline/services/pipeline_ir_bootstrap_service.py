# arvis/kernel/pipeline/services/pipeline_ir_bootstrap_service.py

from __future__ import annotations

from dataclasses import replace
from typing import Any

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.ir.input import CognitiveInputIR
from arvis.ir.context import CognitiveContextIR


class PipelineIRBootstrapService:
    @staticmethod
    def bootstrap_input(
        ctx: CognitivePipelineContext,
    ) -> None:
        if getattr(ctx, "ir_input", None) is not None:
            return

        cognitive_input = getattr(
            ctx,
            "cognitive_input",
            None,
        )

        metadata: dict[str, Any] = (
            dict(cognitive_input)
            if isinstance(cognitive_input, dict)
            else {}
        )

        ctx.ir_input = CognitiveInputIR(
            input_id=str(
                metadata.get(
                    "input_id",
                    f"input::{ctx.user_id}",
                )
            ),
            actor_id=str(
                metadata.get(
                    "actor_id",
                    ctx.user_id,
                )
            ),
            surface_kind=str(
                metadata.get(
                    "surface_kind",
                    "unknown",
                )
            ),
            intent_hint=metadata.get(
                "intent_hint"
            ),
            metadata=metadata,
        )

    @staticmethod
    def bootstrap_context(
        ctx: CognitivePipelineContext,
    ) -> None:
        if getattr(ctx, "ir_context", None) is not None:
            return

        memory_view = (
            getattr(ctx, "memory_projection", None)
            or getattr(ctx, "long_memory", {})
            or {}
        )

        constraints = tuple(
            memory_view.get(
                "constraints",
                [],
            )
            or []
        )

        preferences = (
            memory_view.get(
                "preferences",
                {},
            )
            or {}
        )

        memory_projection = (
            getattr(
                ctx,
                "memory_projection",
                None,
            )
            or {}
        )

        conversation_mode = None

        conversation_context = getattr(
            ctx,
            "conversation_context",
            None,
        )

        if conversation_context is not None:
            conversation_mode = getattr(
                conversation_context,
                "mode",
                None,
            )

        if conversation_mode is None:
            conversation_mode = (
                getattr(
                    ctx,
                    "extra",
                    {},
                ).get(
                    "conversation_mode"
                )
            )

        if conversation_mode is not None:
            conversation_mode = str(
                getattr(
                    conversation_mode,
                    "value",
                    conversation_mode,
                )
            )

        memory_present = bool(
            memory_projection
        )

        memory_pressure = float(
            memory_projection.get(
                "memory_pressure",
                0.0,
            )
            or 0.0
        )

        memory_has_constraints = bool(
            memory_projection.get(
                "has_constraints",
                False,
            )
        )

        memory_constraint_count = len(
            tuple(
                memory_projection.get(
                    "constraints",
                    [],
                )
                or ()
            )
        )

        memory_has_language_pref = bool(
            memory_projection.get(
                "has_language_pref",
                False,
            )
        )

        memory_has_timezone = bool(
            memory_projection.get(
                "has_timezone",
                False,
            )
        )

        ctx.ir_context = CognitiveContextIR(
            user_id=ctx.user_id,
            session_id=getattr(
                ctx,
                "extra",
                {},
            ).get("session_id"),
            conversation_mode=conversation_mode,
            long_memory_constraints=constraints,
            long_memory_preferences=preferences,
            memory_present=memory_present,
            memory_pressure=memory_pressure,
            memory_has_constraints=memory_has_constraints,
            memory_constraint_count=memory_constraint_count,
            memory_has_language_pref=memory_has_language_pref,
            memory_has_timezone=memory_has_timezone,
            extra={
                "memory_pressure": memory_pressure,
                "has_constraints": memory_has_constraints,
                "has_timezone": memory_has_timezone,
                "has_language_pref": memory_has_language_pref,
            },
        )

    @staticmethod
    def refresh_context_extra(
        ctx: CognitivePipelineContext,
    ) -> None:
        ir_context = ctx.ir_context

        if ir_context is None:
            return

        current_extra = dict(
            ir_context.extra or {}
        )

        propagated_keys = (
            "confirmation_override",
        )

        for key in propagated_keys:
            if key in ctx.extra:
                current_extra[key] = (
                    ctx.extra[key]
                )

        ctx.ir_context = replace(
            ir_context,
            extra=current_extra,
        )