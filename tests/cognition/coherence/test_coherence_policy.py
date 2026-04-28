# test/cognition/coherence/test_coherence_policy.py

from arvis.cognition.coherence.change_budget import ChangeBudget
from arvis.cognition.coherence.coherence_policy import CoherencePolicy


class DummySnapshot:
    pass


def test_none_inputs():
    policy = CoherencePolicy()
    assert policy.evaluate(None, None) is None


def test_invalid_budget():
    policy = CoherencePolicy()
    snap = DummySnapshot()

    class Bad:
        current_changes = "x"
        max_changes = "y"

    assert policy.evaluate(snap, Bad()) is None


def test_exceeds_budget():
    policy = CoherencePolicy()
    snap = DummySnapshot()

    budget = ChangeBudget(
        current_changes=10,
        max_changes=1,
        timestamp=0,
    )

    res = policy.evaluate(snap, budget)
    assert res is not None
