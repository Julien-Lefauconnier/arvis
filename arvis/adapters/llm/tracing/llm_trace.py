# arvis/adapters/llm/tracing/llm_trace.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse


@dataclass(frozen=True, slots=True)
class LLMTrace:
    trace_id: str
    syscall: str
    status: Literal["success", "failure"]

    provider: str | None = None
    model: str | None = None
    finish_reason: str | None = None

    prompt_chars: int = 0
    preferred_provider: str | None = None

    total_tokens: int | None = None
    cost: float | None = None
    latency_ms: int | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_response(
        *,
        trace_id: str,
        syscall: str,
        request: LLMRequest,
        response: LLMResponse,
        preferred_provider: str | None = None,
    ) -> LLMTrace:
        usage = response.usage

        return LLMTrace(
            trace_id=trace_id,
            syscall=syscall,
            status="success",
            provider=response.provider,
            model=response.model,
            finish_reason=response.finish_reason,
            prompt_chars=sum(len(m.content or "") for m in (request.messages or [])),
            preferred_provider=preferred_provider,
            total_tokens=None if usage is None else usage.total_tokens,
            cost=None if usage is None else usage.cost,
            latency_ms=None if usage is None else usage.latency_ms,
            metadata={
                "prompt_logged": False,
                "governance": response.metadata.get("llm_governance", {}),
            },
        )
