# tests/adapters/llm/test_llm_tracing.py

from __future__ import annotations

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage
from arvis.adapters.llm.tracing import LLMTrace, serialize_response, serialize_trace


def test_llm_trace_from_response_is_zk_safe() -> None:
    request = LLMRequest(prompt="secret prompt")
    response = LLMResponse(
        content="ok",
        provider="mock",
        model="mock-model",
        usage=LLMUsage(
            prompt_tokens=2,
            completion_tokens=3,
            total_tokens=5,
        ),
        metadata={
            "llm_governance": {
                "allowed": True,
                "risk": "low",
            }
        },
    )

    trace = LLMTrace.from_response(
        trace_id="trace-1",
        syscall="llm.generate",
        request=request,
        response=response,
        preferred_provider="mock",
    )

    serialized = serialize_trace(trace)

    assert serialized["trace_id"] == "trace-1"
    assert serialized["prompt_chars"] == len("secret prompt")
    assert serialized["metadata"]["prompt_logged"] is False
    assert "secret prompt" not in str(serialized)


def test_serialize_response_includes_usage_without_raw() -> None:
    response = LLMResponse(
        content="ok",
        provider="mock",
        model="mock-model",
        raw={"provider_raw": True},
        usage=LLMUsage(
            prompt_tokens=1,
            completion_tokens=2,
            total_tokens=3,
        ),
    )

    serialized = serialize_response(response)

    assert serialized["content"] == "ok"
    assert serialized["usage"]["total_tokens"] == 3
    assert "raw" not in serialized
