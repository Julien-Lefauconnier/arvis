# arvis/adapters/llm/runtime/fallback_executor.py

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

from arvis.adapters.llm.contracts.execution_result import (
    LLMExecutionResult,
    LLMExecutionStatus,
    ProviderAttempt,
)
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.providers.base import BaseLLMProvider
from arvis.errors import normalize_error
from arvis.errors.llm_runtime import (
    LLMEmptyResponseError,
    LLMFallbackExhaustedError,
)


class LLMFallbackExecutionError(LLMFallbackExhaustedError):
    """Raised when all providers fail."""


@dataclass(slots=True)
class FallbackExecutor:
    """
    Production-grade sequential fallback executor.

    Strategy:
    - try providers in declared order
    - first successful response wins
    - collect telemetry for every attempt
    - raise deterministic error if all fail
    """

    providers: Sequence[BaseLLMProvider]
    fail_fast_on_empty: bool = True

    def execute(self, request: LLMRequest) -> LLMExecutionResult:
        if not self.providers:
            raise LLMFallbackExecutionError("no_llm_providers_configured")

        attempts: list[ProviderAttempt] = []

        for provider in self.providers:
            provider_name = type(provider).__name__
            started = perf_counter()

            try:
                response = provider.generate(request)

                latency_ms = (perf_counter() - started) * 1000.0

                if self.fail_fast_on_empty and not response.content.strip():
                    raise LLMEmptyResponseError("empty_llm_response")

                attempts.append(
                    ProviderAttempt(
                        provider=provider_name,
                        success=True,
                        latency_ms=latency_ms,
                    )
                )

                metadata = dict(response.metadata)
                metadata["fallback"] = {
                    "selected_provider": provider_name,
                    "attempt_count": len(attempts),
                    "attempts": [
                        {
                            "provider": a.provider,
                            "success": a.success,
                            "latency_ms": a.latency_ms,
                            "error": a.error,
                        }
                        for a in attempts
                    ],
                }

                final_response = LLMResponse(
                    content=response.content,
                    provider=response.provider,
                    model=response.model,
                    usage=response.usage,
                    metadata=metadata,
                )

                return LLMExecutionResult(
                    status=LLMExecutionStatus.FALLBACK_USED,
                    response=final_response,
                    retry_count=0,
                    fallback_used=len(attempts) > 1,
                    provider_attempts=tuple(attempts),
                    evaluation={},
                    observation={},
                    error=None,
                    degraded=False,
                    replay_safe=False,
                    require_confirmation=False,
                )

            except Exception as exc:
                latency_ms = (perf_counter() - started) * 1000.0

                attempts.append(
                    ProviderAttempt(
                        provider=provider_name,
                        success=False,
                        latency_ms=latency_ms,
                        error=normalize_error(exc).code,
                    )
                )

        raise LLMFallbackExecutionError(f"all_llm_providers_failed:{len(attempts)}")
