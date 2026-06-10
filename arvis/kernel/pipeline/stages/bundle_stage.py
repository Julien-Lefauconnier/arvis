# arvis/kernel/pipeline/stages/bundle_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot
from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.retrieval.cognitive_retrieval_snapshot import (
    CognitiveRetrievalSnapshot,
)


class BundleStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        introspection = ctx.introspection or IntrospectionSnapshot()
        explanation = ctx.explanation or ExplanationSnapshot()

        memory_projection = getattr(ctx, "memory_projection", None)
        memory_long = getattr(ctx, "memory_long", None)

        # Perception -> governance seam (decision B): veramem may surface a
        # ZKCS-safe retrieval snapshot under ctx.extra["retrieval_snapshot"]
        # (same shared-extra channel as scientific_state). Fail-safe: absent
        # or wrong type => None, leaving prior behavior unchanged.
        retrieval_snapshot = self._retrieval_snapshot(ctx)

        bundle = pipeline.bundle_builder.build(
            decision_result=ctx.decision_layer.decision_result,
            introspection=introspection,
            explanation=explanation,
            timeline=ctx.timeline,
            memory_long=memory_long,
            retrieval_snapshot=retrieval_snapshot,
            memory=memory_projection,
        )

        ctx.decision_layer.bundle = bundle

    @staticmethod
    def _retrieval_snapshot(ctx: Any) -> CognitiveRetrievalSnapshot | None:
        extra = getattr(ctx, "extra", None)
        if not isinstance(extra, dict):
            return None
        candidate = extra.get("retrieval_snapshot")
        if isinstance(candidate, CognitiveRetrievalSnapshot):
            return candidate
        return None
