# tests/adapters/llm/contracts/test_result.py

import pytest
from pydantic import ValidationError

from arvis.adapters.llm.contracts.error_payload import LLMErrorPayload
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.result import LLMResult
from arvis.adapters.llm.contracts.usage import LLMUsage


def test_success_result():
    resp = LLMResponse(
        content="OK",
        provider="test",
        model="mock",
        usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
    )

    result = LLMResult(success=True, response=resp)

    assert result.success is True
    assert result.response is not None
    assert result.error is None


def test_error_result():
    err = LLMErrorPayload(
        code="timeout",
        message="timeout",
        error_type="LLMProviderError",
    )

    result = LLMResult(success=False, error=err)

    assert result.error.code == "timeout"


def test_immutable():
    result = LLMResult(success=True)
    with pytest.raises(ValidationError):
        result.success = False
