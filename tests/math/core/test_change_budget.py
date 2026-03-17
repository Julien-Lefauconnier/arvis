# tests/math/core/test_change_budget.py

from arvis.math.core.change_budget import ChangeBudget


def test_budget_initial_state():

    b = ChangeBudget(1.0)

    assert b.consumption == 0.0
    assert b.remaining == 1.0
    assert not b.exhausted


def test_budget_consumption():

    b = ChangeBudget(1.0)

    b2 = b.consume(0.3)

    assert b2.consumption == 0.3
    assert 0.69 < b2.remaining < 0.71
    assert not b2.exhausted


def test_budget_exhaustion():

    b = ChangeBudget(1.0)

    b = b.consume(0.5)
    b = b.consume(0.5)

    assert b.exhausted
    assert b.remaining == 0.0


def test_budget_can_consume():

    b = ChangeBudget(1.0)

    assert b.can_consume(0.5)

    b = b.consume(0.8)

    assert not b.can_consume(0.3)