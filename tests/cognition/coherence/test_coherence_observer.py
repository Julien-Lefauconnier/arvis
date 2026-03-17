# tests/cognition/coherence/test_coherence_observer.py

from types import SimpleNamespace

from arvis.cognition.coherence.coherence_observer import (
    CoherenceObserver,
)


def make_bundle(reason="r", actions=None):
    if actions is None:
        actions = []

    decision = SimpleNamespace(
        reason=reason,
        proposed_actions=actions,
        memory_intent="none",
        conflicts=[],
        knowledge_snapshot=None,
        uncertainty_frames=[],
        context_hints={},
    )

    bundle = SimpleNamespace(
        decision_result=decision,
        context_hints={},
    )

    return bundle


def test_signature_extraction():
    bundle = make_bundle(reason="test_reason")

    sig = CoherenceObserver.signature(bundle)

    assert sig.reason == "test_reason"
    assert isinstance(sig.proposed_action_ids, set)
    assert isinstance(sig.context_hint_keys, set)


def test_distance_zero_when_identical():
    b1 = make_bundle()
    b2 = make_bundle()

    s1 = CoherenceObserver.signature(b1)
    s2 = CoherenceObserver.signature(b2)

    d = CoherenceObserver.distance(s1, s2)

    assert d == 0


def test_distance_detects_reason_change():
    b1 = make_bundle(reason="A")
    b2 = make_bundle(reason="B")

    s1 = CoherenceObserver.signature(b1)
    s2 = CoherenceObserver.signature(b2)

    d = CoherenceObserver.distance(s1, s2)

    assert d >= 1


def test_update_budget_first_cycle():
    bundle = make_bundle()

    budget = CoherenceObserver.update_budget(
        previous_bundle=None,
        current_bundle=bundle,
        previous_budget=None,
    )

    assert budget.current_changes == 0


def test_update_budget_detects_change():
    b1 = make_bundle(reason="A")
    b2 = make_bundle(reason="B")

    budget = CoherenceObserver.update_budget(
        previous_bundle=b1,
        current_bundle=b2,
        previous_budget=None,
    )

    assert budget.current_changes >= 1