# tests/cognition/test_cognitive_bundle_memory.py

from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder


def test_bundle_accepts_memory_projection():
    builder = CognitiveBundleBuilder()

    bundle = builder.build(
        decision_result={},
        introspection=None,
        explanation=None,
        timeline=[],
        memory={
            "preferences": {"language": True},
            "constraints": ["no_tracking"],
            "memory_pressure": 2,
            "has_constraints": True,
        },
    )

    assert hasattr(bundle, "memory_features")
    assert bundle.memory_features["has_constraints"] is True
    assert bundle.memory_features["memory_pressure"] == 2


def test_bundle_memory_optional():
    builder = CognitiveBundleBuilder()

    bundle = builder.build(
        decision_result={},
        introspection=None,
        explanation=None,
        timeline=[],
    )

    assert hasattr(bundle, "memory_features")
    assert bundle.memory_features == {}
