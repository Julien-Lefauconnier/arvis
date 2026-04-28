# tests/cognition/test_cognitive_bundle_coherence.py

from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.decision.decision_result import DecisionResult
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot
from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.timeline.timeline_hashchain import TimelineHashChain
from arvis.timeline.timeline_snapshot import TimelineSnapshot


def _dummy_timeline():
    entries = ()
    chain = TimelineHashChain(())
    return TimelineSnapshot(entries, chain)


def test_cognitive_bundle_coherence():
    bundle = CognitiveBundleSnapshot(
        decision_result=DecisionResult(None),
        introspection=IntrospectionSnapshot(),
        explanation=ExplanationSnapshot(),
        timeline=_dummy_timeline(),
    )

    assert bundle.decision_result is not None
    assert bundle.introspection is not None
    assert bundle.explanation is not None
    assert bundle.timeline is not None
