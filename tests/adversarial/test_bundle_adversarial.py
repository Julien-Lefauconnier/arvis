# tests/adversarial/test_bundle_adversarial.py

import pytest

from arvis.cognition.bundle.cognitive_bundle_invariants import (
    CognitiveBundleInvariantError,
    assert_cognitive_bundle_invariants,
)


class BadObject:
    pass


class Dummy:
    def __init__(self):
        self.decision_result = None
        self.introspection = None
        self.explanation = type("E", (), {"items": []})()
        self.timeline = []
        self.memory_long = None
        self.retrieval_snapshot = None
        self.generated_at = None
        self.context_hints = {"bad": BadObject()}


def test_context_hints_poisoning():
    bundle = Dummy()

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)
