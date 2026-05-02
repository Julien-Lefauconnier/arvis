# arvis/adapters/llm/tracing/serializer.py

from __future__ import annotations

from typing import Any

from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage
from arvis.adapters.llm.tracing.llm_trace import LLMTrace


def serialize_usage(usage: LLMUsage | None) -> dict[str, Any] | None:
    if usage is None:
        return None

    return {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "cost": usage.cost,
        "latency_ms": usage.latency_ms,
        "provider": usage.provider,
        "model": usage.model,
    }


def serialize_response(response: LLMResponse) -> dict[str, Any]:
    return {
        "content": response.content,
        "provider": response.provider,
        "model": response.model,
        "finish_reason": response.finish_reason,
        "trace_id": response.trace_id,
        "metadata": response.metadata,
        "usage": serialize_usage(response.usage),
    }


def serialize_trace(trace: LLMTrace) -> dict[str, Any]:
    return {
        "trace_id": trace.trace_id,
        "syscall": trace.syscall,
        "status": trace.status,
        "provider": trace.provider,
        "model": trace.model,
        "finish_reason": trace.finish_reason,
        "prompt_chars": trace.prompt_chars,
        "preferred_provider": trace.preferred_provider,
        "total_tokens": trace.total_tokens,
        "cost": trace.cost,
        "latency_ms": trace.latency_ms,
        "metadata": trace.metadata,
    }
