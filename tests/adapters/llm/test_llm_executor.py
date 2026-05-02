# tests/adapters/llm/test_llm_executor.py

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.providers.base import BaseLLMProvider
from arvis.adapters.llm.runtime.executor import LLMRuntimeExecutor


class FailingProvider(BaseLLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        raise RuntimeError("boom")


class SuccessProvider(BaseLLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=f"fallback:{request.prompt}",
            metadata={"provider": "success"},
        )


def test_runtime_executor_uses_mock_provider() -> None:
    executor = LLMRuntimeExecutor()

    response = executor.execute(
        LLMRequest(prompt="hello"),
        preferred_provider="mock",
    )

    assert response.content == "mock:hello"


def test_runtime_executor_returns_response_metadata() -> None:
    executor = LLMRuntimeExecutor()

    response = executor.execute(
        LLMRequest(prompt="ping"),
        preferred_provider="mock",
    )

    assert response.metadata["provider"] == "mock"


def test_runtime_executor_uses_fallback_providers() -> None:
    executor = LLMRuntimeExecutor(
        fallback_providers=[
            FailingProvider(),
            SuccessProvider(),
        ]
    )

    response = executor.execute(LLMRequest(prompt="hello"))

    assert response.content == "fallback:hello"
    assert response.metadata["provider"] == "success"
    fallback = response.metadata["fallback"]

    assert fallback["selected_provider"] == "SuccessProvider"
    assert fallback["attempt_count"] == 2
