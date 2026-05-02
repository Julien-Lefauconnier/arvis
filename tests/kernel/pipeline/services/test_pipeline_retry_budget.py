# tests/kernel/pipeline/services/test_pipeline_retry_budget.py

from __future__ import annotations

import pytest

from arvis.kernel.pipeline.services.pipeline_retry_budget import PipelineRetryBudget


def test_retry_budget_allows_when_remaining() -> None:
    budget = PipelineRetryBudget(max_retries=2)

    decision = budget.decide(consumed_retries=1)

    assert decision.allowed is True
    assert decision.reason == "retry_budget_available"
    assert decision.remaining == 1


def test_retry_budget_blocks_when_exhausted() -> None:
    budget = PipelineRetryBudget(max_retries=1)

    decision = budget.decide(consumed_retries=1)

    assert decision.allowed is False
    assert decision.reason == "retry_budget_exhausted"
    assert decision.remaining == 0


def test_retry_budget_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        PipelineRetryBudget(max_retries=-1)

    budget = PipelineRetryBudget(max_retries=1)

    with pytest.raises(ValueError):
        budget.decide(consumed_retries=-1)
