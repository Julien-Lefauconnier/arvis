# tests/adapters/llm/test_fallback_executor.py

from __future__ import annotations

import pytest

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.providers.base import BaseLLMProvider
from arvis.adapters.llm.runtime.fallback_executor import (
    FallbackExecutionResult,
    FallbackExecutor,
    LLMFallbackExecutionError,
)


class SuccessProvider(BaseLLMProvider):
    def __init__(self, content: str = "ok") -> None:
        self.calls = 0
        self._content = content

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            content=self._content,
            raw={},
            metadata={},
        )


class FailingProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        raise RuntimeError("provider_failure")


def test_success_first_provider_short_circuits() -> None:
    first = SuccessProvider("hello")
    second = SuccessProvider("unused")

    executor = FallbackExecutor(
        providers=[first, second],
    )

    result = executor.execute(
        LLMRequest(prompt="test")
    )

    assert isinstance(result, FallbackExecutionResult)
    assert result.response.content == "hello"

    assert first.calls == 1
    assert second.calls == 0

    fallback = result.response.metadata["fallback"]

    assert (
        fallback["selected_provider"]
        == "SuccessProvider"
    )
    assert result.response.metadata["fallback"]["attempt_count"] == 1


def test_second_provider_used_after_first_failure() -> None:
    first = FailingProvider()
    second = SuccessProvider("recovered")

    executor = FallbackExecutor(
        providers=[first, second],
    )

    result = executor.execute(
        LLMRequest(prompt="test")
    )

    assert result.response.content == "recovered"

    assert first.calls == 1
    assert second.calls == 1

    assert result.response.metadata["fallback"]["attempt_count"] == 2

    attempts = result.response.metadata["fallback"]["attempts"]

    assert attempts[0]["success"] is False
    assert attempts[1]["success"] is True


def test_all_providers_fail_raises() -> None:
    executor = FallbackExecutor(
        providers=[
            FailingProvider(),
            FailingProvider(),
        ],
    )

    with pytest.raises(LLMFallbackExecutionError):
        executor.execute(
            LLMRequest(prompt="test")
        )


def test_empty_response_falls_back_when_enabled() -> None:
    first = SuccessProvider("")
    second = SuccessProvider("real")

    executor = FallbackExecutor(
        providers=[first, second],
        fail_fast_on_empty=True,
    )

    result = executor.execute(
        LLMRequest(prompt="test")
    )

    assert result.response.content == "real"
    assert result.response.metadata["fallback"]["attempt_count"] == 2


def test_empty_response_allowed_when_disabled() -> None:
    first = SuccessProvider("")

    executor = FallbackExecutor(
        providers=[first],
        fail_fast_on_empty=False,
    )

    result = executor.execute(
        LLMRequest(prompt="test")
    )

    assert result.response.content == ""
    assert result.response.metadata["fallback"]["attempt_count"] == 1


def test_no_provider_configured_raises() -> None:
    executor = FallbackExecutor(providers=[])

    with pytest.raises(LLMFallbackExecutionError):
        executor.execute(
            LLMRequest(prompt="test")
        )