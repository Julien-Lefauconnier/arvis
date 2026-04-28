# tests/cognition/coherence/test_change_budget.py

from arvis.cognition.coherence.change_budget import ChangeBudget


def test_change_budget_creation():
    budget = ChangeBudget(
        max_changes=10,
        current_changes=3,
        timestamp=123,
    )

    assert budget.max_changes == 10
    assert budget.current_changes == 3
    assert budget.timestamp == 123


def test_change_budget_to_dict():
    budget = ChangeBudget(
        max_changes=5,
        current_changes=2,
        timestamp=42,
    )

    d = budget.to_dict()

    assert d["max_changes"] == 5
    assert d["current_changes"] == 2
    assert d["timestamp"] == 42


def test_change_budget_is_immutable():
    budget = ChangeBudget(
        max_changes=5,
        current_changes=1,
        timestamp=0,
    )

    try:
        budget.current_changes = 10
        assert False
    except Exception:
        assert True
