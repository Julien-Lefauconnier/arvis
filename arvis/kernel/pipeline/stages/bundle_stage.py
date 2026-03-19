# arvis/kernel/pipeline/stages/bundle_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot


class BundleStage:
    """
    Stage 3: bundle construction.

    Responsibilities:
    - normalize optional introspection/explanation inputs
    - build the cognitive bundle
    - attach the bundle to ctx
    """

    def run(self, pipeline: Any, ctx: Any) -> None:
        introspection = ctx.introspection or IntrospectionSnapshot()
        explanation = ctx.explanation or ExplanationSnapshot()

        bundle = pipeline.bundle_builder.build(
            decision_result=ctx.decision_result,
            introspection=introspection,
            explanation=explanation,
            timeline=ctx.timeline,
        )

        ctx.bundle = bundle