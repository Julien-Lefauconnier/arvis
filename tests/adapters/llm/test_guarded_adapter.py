# tests/adapters/llm/test_guarded_adapter.py

from __future__ import annotations

import pytest

from arvis.adapters.llm.contracts.errors import LLMPolicyViolation
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage
from arvis.adapters.llm.governance.budget import LLMBudget
from arvis.adapters.llm.governance.policy import LLMGovernancePolicy
from arvis.adapters.llm.governance.risk import LLMRisk, LLMRiskLevel
from arvis.adapters.llm.runtime.guarded_adapter import GuardedLLMAdapter


class DummyExecutor:
    def execute(self, request, *, preferred_provider=None):
        return LLMResponse(
            content="ok",
            raw={},
            metadata={},
        )


class BudgetOverflowExecutor:
    def execute(self, request, *, preferred_provider=None):
        return LLMResponse(
            content="ok",
            raw={},
            usage=LLMUsage(
                prompt_tokens=100,
                completion_tokens=100,
                total_tokens=200,
            ),
            metadata={},
        )


def test_guarded_adapter_success() -> None:
    adapter = GuardedLLMAdapter(
        executor=DummyExecutor(),
    )

    response = adapter.generate(LLMRequest(prompt="hello"))

    assert response.content == "ok"
    assert response.metadata["llm_governance"]["allowed"] is True


def test_guarded_adapter_policy_block() -> None:
    adapter = GuardedLLMAdapter(
        executor=DummyExecutor(),
        policy=LLMGovernancePolicy(
            allow_llm=True,
            blocked_terms={"forbidden"},
        ),
    )

    with pytest.raises(LLMPolicyViolation):
        adapter.generate(LLMRequest(prompt="forbidden request"))


def test_guarded_adapter_budget_exceeded():
    adapter = GuardedLLMAdapter(
        executor=BudgetOverflowExecutor(),
        budget=LLMBudget(max_tokens=1),
    )

    request = LLMRequest(prompt="test")

    with pytest.raises(LLMPolicyViolation):
        adapter.generate(request)


def test_guarded_adapter_risk_block():
    adapter = GuardedLLMAdapter(
        max_risk=LLMRiskLevel.LOW,
    )

    request = LLMRequest(prompt="test")

    # override internal risk method
    adapter = GuardedLLMAdapter(
        max_risk=LLMRiskLevel.LOW,
        risk_evaluator=lambda _: LLMRisk(LLMRiskLevel.HIGH),
    )

    with pytest.raises(LLMPolicyViolation):
        adapter.generate(request)


def test_guarded_adapter_metadata_enrichment():
    adapter = GuardedLLMAdapter()

    request = LLMRequest(prompt="hello")

    response = adapter.generate(request)

    assert "llm_governance" in response.metadata
    assert "llm" in response.metadata
