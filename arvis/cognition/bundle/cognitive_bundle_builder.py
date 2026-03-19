# arvis/cognition/bundle/cognitive_bundle_builder.py

from datetime import datetime, timezone
from typing import Optional, Sequence

from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.bundle.cognitive_bundle_invariants import assert_cognitive_bundle_invariants
from arvis.cognition.decision.decision_result import DecisionResult
from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot
from arvis.cognition.retrieval.cognitive_retrieval_snapshot import CognitiveRetrievalSnapshot
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot
from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_snapshot import TimelineSnapshot

class CognitiveBundleBuilder:
    """
    Declarative CognitiveBundle builder.

    Kernel guarantees:
    - no reasoning
    - no execution
    - deterministic construction
    """

    @staticmethod
    def build(
        *,
        decision_result: DecisionResult,
        introspection: IntrospectionSnapshot,
        explanation: ExplanationSnapshot,
        timeline: Sequence[TimelineEntry],
        memory_long: Optional[MemoryLongSnapshot] = None,
        retrieval_snapshot: Optional[CognitiveRetrievalSnapshot] = None,
        generated_at: Optional[datetime] = None,
    ) -> CognitiveBundleSnapshot:

        bundle = CognitiveBundleSnapshot(
            decision_result=decision_result,
            introspection=introspection,
            explanation=explanation,
            timeline=timeline,
            memory_long=memory_long,
            retrieval_snapshot=retrieval_snapshot,
            context_hints=decision_result.context_hints,
            generated_at=generated_at or datetime.now(timezone.utc),
        )

        assert_cognitive_bundle_invariants(bundle)

        return bundle
    
    # ------------------------------------------------------------------
    # Replay reconstruction API
    # ------------------------------------------------------------------

    @classmethod
    def from_timeline(cls, snapshot: TimelineSnapshot) -> CognitiveBundleSnapshot:
        """
        Deterministic reconstruction from a TimelineSnapshot.

        Used by:
        - ReplayEngine
        - simulations
        - audit / deterministic replay

        This intentionally produces a minimal valid bundle.
        """

        decision = DecisionResult.empty()

        ts = snapshot.entries[-1].created_at if snapshot.entries else None

        introspection = IntrospectionSnapshot(
            created_at=ts or datetime.now(timezone.utc)
        )

        explanation = ExplanationSnapshot(
            created_at=ts or datetime.now(timezone.utc)
        )

        return cls.build(
            decision_result=decision,
            introspection=introspection,
            explanation=explanation,
            timeline=snapshot.entries,
            memory_long=None,
            retrieval_snapshot=None,
            generated_at=ts,
        )