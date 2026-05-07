# tests/adapters/llm/test_llm_executor.py

from arvis.adapters.llm.contracts.message import LLMMessage
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


def test_executor_injects_evaluation_metadata():
    from arvis.adapters.llm.contracts.request import LLMRequest
    from arvis.adapters.llm.runtime.executor import LLMRuntimeExecutor

    class DummyProvider:
        def generate(self, request):
            return LLMResponse(
                content="ok",
                metadata={
                    "logprobs": [-1.0, -0.5],
                    "token_count": 5,
                },
            )

    executor = LLMRuntimeExecutor()
    executor._router = type("R", (), {"route": lambda *_: DummyProvider()})()

    response = executor.execute(
        LLMRequest(messages=[LLMMessage(role="user", content="test")])
    )

    assert "llm_evaluation" in response.metadata
    assert "accept" in response.metadata["llm_evaluation"]


def test_executor_injects_llm_evaluation():
    executor = LLMRuntimeExecutor()

    class DummyProvider:
        def generate(self, request):
            return LLMResponse(
                content="ok",
                metadata={"logprobs": [-1.0, -0.5]},
            )

    executor._router = type("R", (), {"route": lambda *_: DummyProvider()})()

    response = executor.execute(
        LLMRequest(messages=[LLMMessage(role="user", content="hi")])
    )

    assert "llm_evaluation" in response.metadata


def test_executor_retry_path():
    class RetryEvaluator:
        def evaluate(self, obs):
            return type(
                "D",
                (),
                {
                    "accept": False,
                    "retry": True,
                    "fallback": False,
                    "require_confirmation": False,
                },
            )()

    executor = LLMRuntimeExecutor()
    executor._evaluator = RetryEvaluator()

    calls = {"count": 0}

    class DummyProvider:
        def generate(self, request):
            calls["count"] += 1
            return LLMResponse(content="ok", metadata={})

    executor._router = type("R", (), {"route": lambda *_: DummyProvider()})()

    executor.execute(LLMRequest(messages=[LLMMessage(role="user", content="test")]))

    assert calls["count"] == 2


def test_executor_fallback_path():
    class FallbackEvaluator:
        def evaluate(self, obs):
            return type(
                "D",
                (),
                {
                    "accept": False,
                    "retry": False,
                    "fallback": True,
                    "require_confirmation": False,
                },
            )()

    class ProviderA:
        def generate(self, request):
            return LLMResponse(content="a", metadata={})

    class ProviderB:
        def generate(self, request):
            return LLMResponse(content="b", metadata={})

    executor = LLMRuntimeExecutor(fallback_providers=[ProviderB()])
    executor._evaluator = FallbackEvaluator()
    executor._router = type("R", (), {"route": lambda *_: ProviderA()})()

    response = executor.execute(
        LLMRequest(messages=[LLMMessage(role="user", content="test")])
    )

    assert response.content == "b"


def test_executor_fallback_retry_path():
    class RetryEvaluator:
        def evaluate(self, obs):
            return type(
                "D",
                (),
                {
                    "accept": False,
                    "retry": True,
                    "fallback": False,
                    "require_confirmation": False,
                },
            )()

    calls = {"count": 0}

    class Provider:
        def generate(self, request):
            calls["count"] += 1
            return LLMResponse(content="ok", metadata={})

    executor = LLMRuntimeExecutor(fallback_providers=[Provider()])
    executor._evaluator = RetryEvaluator()

    executor.execute(LLMRequest(messages=[LLMMessage(role="user", content="test")]))

    # fallback executor appelé 2 fois
    assert calls["count"] == 2
