# tests/integration/test_system_serialization.py

import pickle

from arvis.timeline.timeline_snapshot import TimelineSnapshot
from arvis.timeline.timeline_hashchain import TimelineHashChain

from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.decision.decision_result import DecisionResult
from arvis.cognition.introspection.introspection_snapshot import IntrospectionSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot


def test_full_system_pickle_roundtrip():

    timeline = TimelineSnapshot((), TimelineHashChain(()))

    bundle = CognitiveBundleSnapshot(
        decision_result=DecisionResult(None),
        introspection=IntrospectionSnapshot(),
        explanation=ExplanationSnapshot(),
        timeline=timeline,
    )

    data = pickle.dumps(bundle)

    restored = pickle.loads(data)

    assert restored == bundle