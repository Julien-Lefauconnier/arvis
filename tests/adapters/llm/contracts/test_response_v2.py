# tests/adapters/llm/contracts/test_response_v2.py

import pytest
from pydantic import ValidationError

from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage


def test_valid_response():
    resp = LLMResponse(
        content="Hello",
        provider="openai",
        model="gpt-4",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
    assert resp.content == "Hello"


def test_metadata_default():
    resp = LLMResponse(
        content="Hi",
        provider="test",
        model="mock",
        usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
    )
    assert resp.metadata == {}


def test_immutable():
    resp = LLMResponse(
        content="Hello",
        provider="openai",
        model="gpt-4",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
    with pytest.raises(ValidationError):
        resp.content = "Changed"
