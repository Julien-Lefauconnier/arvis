# tests/adapters/llm/test_guarded_adapter.py

from __future__ import annotations

import pytest

from arvis.adapters.llm.contracts.errors import LLMPolicyViolation
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.governance.policy import LLMGovernancePolicy
from arvis.adapters.llm.runtime.guarded_adapter import GuardedLLMAdapter


class DummyExecutor:
    def execute(self, request, *, preferred_provider=None):
        return LLMResponse(
            content="ok",
            raw={},
            metadata={},
        )


def test_guarded_adapter_success() -> None:
    adapter = GuardedLLMAdapter(
        executor=DummyExecutor(),
    )

    response = adapter.generate(
        LLMRequest(prompt="hello")
    )

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
        adapter.generate(
            LLMRequest(prompt="forbidden request")
        )