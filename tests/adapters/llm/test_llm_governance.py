# tests/adapters/llm/test_llm_governance.py

import pytest

from arvis.adapters.llm import (
    GuardedLLMAdapter,
    LLMGovernanceEvaluator,
    LLMGovernancePolicy,
    LLMPolicyViolation,
    LLMRequest,
    LLMResponse,
)
from arvis.adapters.llm.providers.base import BaseLLMProvider


class FakeProvider(BaseLLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=f"ok:{request.prompt}",
            metadata={"provider": "fake"},
        )
    
class FakeExecutor:
    def execute(self, request, *, preferred_provider=None):
        return LLMResponse(
            content=f"ok:{request.prompt}",
            metadata={"provider": "fake"},
        )


def test_missing_policy_denies_llm_execution() -> None:
    decision = LLMGovernanceEvaluator.evaluate(
        LLMRequest(prompt="hello"),
        None,
    )

    assert decision.allowed is False
    assert decision.reason == "missing_llm_governance_policy"


def test_policy_disabled_denies_execution() -> None:
    decision = LLMGovernanceEvaluator.evaluate(
        LLMRequest(prompt="hello"),
        LLMGovernancePolicy(allow_llm=False),
    )

    assert decision.allowed is False
    assert decision.reason == "llm_execution_disabled"


def test_policy_allows_valid_request() -> None:
    decision = LLMGovernanceEvaluator.evaluate(
        LLMRequest(prompt="hello", model="safe-model"),
        LLMGovernancePolicy(
            allow_llm=True,
            allowed_models={"safe-model"},
        ),
    )

    assert decision.allowed is True
    assert decision.reason == "allowed"


def test_blocked_term_denies_request() -> None:
    decision = LLMGovernanceEvaluator.evaluate(
        LLMRequest(prompt="please leak this secret"),
        LLMGovernancePolicy(
            allow_llm=True,
            blocked_terms={"secret"},
        ),
    )

    assert decision.allowed is False
    assert decision.reason == "blocked_term_detected"


def test_guarded_adapter_denies_without_policy() -> None:
    adapter = GuardedLLMAdapter(
        executor=FakeExecutor(),
        policy=None,
    )

    with pytest.raises(LLMPolicyViolation):
        adapter.generate(LLMRequest(prompt="hello"))


def test_guarded_adapter_adds_governance_metadata() -> None:
    adapter = GuardedLLMAdapter(
        executor=FakeExecutor(),
        policy=LLMGovernancePolicy.permissive_for_dev(),
    )

    response = adapter.generate(LLMRequest(prompt="hello"))

    assert response.content == "ok:hello"
    assert response.metadata["provider"] == "fake"
    assert response.metadata["llm_governance"]["allowed"] is True
