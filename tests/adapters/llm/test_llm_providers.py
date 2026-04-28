# tests/adapters/llm/test_llm_providers.py

from arvis.adapters.llm import LLMRequest
from arvis.adapters.llm.providers import MockLLMProvider


def test_mock_provider_is_deterministic() -> None:
    provider = MockLLMProvider()

    request = LLMRequest(prompt="hello")

    r1 = provider.generate(request)
    r2 = provider.generate(request)

    assert r1.content == r2.content
    assert r1.metadata["provider"] == "mock"


def test_mock_provider_supports_custom_prefix() -> None:
    provider = MockLLMProvider(prefix="dev")

    response = provider.generate(LLMRequest(prompt="ping"))

    assert response.content == "dev:ping"
