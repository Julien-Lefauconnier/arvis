# tests/unit/llm/test_budget.py

from arvis.adapters.llm.governance.budget import LLMBudget


def test_budget_allows_tokens():
    budget = LLMBudget(max_tokens=100)

    assert budget.allows_tokens(50)
    assert not budget.allows_tokens(150)


def test_budget_allows_cost():
    budget = LLMBudget(max_cost=0.05)

    assert budget.allows_cost(0.01)
    assert not budget.allows_cost(0.1)


def test_budget_combined():
    budget = LLMBudget(max_tokens=100, max_cost=0.05)

    assert budget.is_within(tokens=50, cost=0.01)
    assert not budget.is_within(tokens=150, cost=0.01)
    assert not budget.is_within(tokens=50, cost=0.1)


def test_budget_no_limits():
    budget = LLMBudget()

    assert budget.is_within(tokens=10, cost=10.0)
