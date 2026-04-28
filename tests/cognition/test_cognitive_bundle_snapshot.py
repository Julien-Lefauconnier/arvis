# tests/cognition/test_cognitive_bundle_snapshot.py

from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.decision.decision_result import DecisionResult
from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot
from arvis.timeline.timeline_snapshot import TimelineSnapshot
from arvis.timeline.timeline_hashchain import TimelineHashChain


def _dummy_timeline():
    entries = ()
    chain = TimelineHashChain(())
    return TimelineSnapshot(entries, chain)


def test_bundle_snapshot_creation():
    snap = CognitiveBundleSnapshot(
        decision_result=DecisionResult(None),
        introspection=IntrospectionSnapshot(),
        explanation=ExplanationSnapshot(),
        timeline=_dummy_timeline(),
    )

    assert snap is not None


def test_bundle_snapshot_immutable():
    snap = CognitiveBundleSnapshot(
        decision_result=DecisionResult(None),
        introspection=IntrospectionSnapshot(),
        explanation=ExplanationSnapshot(),
        timeline=_dummy_timeline(),
    )

    try:
        snap.test = 1
        mutated = True
    except Exception:
        mutated = False

    assert mutated is False
