# tests/cognition/coherence/test_stability_constraint.py

from arvis.cognition.coherence.change_budget import ChangeBudget
from arvis.cognition.coherence.stability_constraint import StabilityConstraint


def test_stability_constraint_stable():
    budget = ChangeBudget(
        max_changes=10,
        current_changes=7,
        timestamp=1,
    )

    result = StabilityConstraint.evaluate(budget)

    assert result.stable is True
    assert result.violation == 0
    assert "Within change budget" in result.rationale


def test_stability_constraint_violation():
    budget = ChangeBudget(
        max_changes=10,
        current_changes=15,
        timestamp=1,
    )

    result = StabilityConstraint.evaluate(budget)

    assert result.stable is False
    assert result.violation == 5


def test_stability_constraint_should_warn():
    budget = ChangeBudget(
        max_changes=10,
        current_changes=12,
        timestamp=1,
    )

    assert StabilityConstraint.should_warn(budget) is True


def test_stability_constraint_should_abstain_threshold():
    budget = ChangeBudget(
        max_changes=10,
        current_changes=20,
        timestamp=1,
    )

    assert StabilityConstraint.should_abstain(budget, hard_threshold=5) is True
