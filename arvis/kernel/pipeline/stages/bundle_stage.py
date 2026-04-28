# arvis/kernel/pipeline/stages/bundle_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot


class BundleStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        introspection = ctx.introspection or IntrospectionSnapshot()
        explanation = ctx.explanation or ExplanationSnapshot()

        memory_projection = getattr(ctx, "memory_projection", None)
        memory_long = getattr(ctx, "memory_long", None)

        bundle = pipeline.bundle_builder.build(
            decision_result=ctx.decision_result,
            introspection=introspection,
            explanation=explanation,
            timeline=ctx.timeline,
            memory_long=memory_long,
            memory=memory_projection,
        )

        ctx.bundle = bundle
