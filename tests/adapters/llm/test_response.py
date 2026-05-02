# tests/unit/llm/test_response.py

from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage


def test_response_basic():
    response = LLMResponse(content="hello")

    assert response.content == "hello"
    assert not response.is_empty()


def test_response_empty():
    response = LLMResponse(content="   ")
    assert response.is_empty()


def test_response_with_usage():
    usage = LLMUsage(10, 10, 20)

    response = LLMResponse(
        content="ok",
        usage=usage,
        provider="openai",
        model="gpt-4o",
    )

    assert response.usage.total_tokens == 20
    assert response.provider == "openai"
