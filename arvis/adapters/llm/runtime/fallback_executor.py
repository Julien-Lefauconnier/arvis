# arvis/adapters/llm/runtime/fallback_executor.py

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.providers.base import BaseLLMProvider


class LLMFallbackExecutionError(RuntimeError):
    """Raised when all providers fail."""


@dataclass(frozen=True, slots=True)
class ProviderAttempt:
    provider: str
    success: bool
    latency_ms: float
    error: str | None = None


@dataclass(frozen=True, slots=True)
class FallbackExecutionResult:
    response: LLMResponse
    attempts: tuple[ProviderAttempt, ...]


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

    def execute(self, request: LLMRequest) -> FallbackExecutionResult:
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
                    raise RuntimeError("empty_llm_response")

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
                    raw=response.raw,
                    metadata=metadata,
                )

                return FallbackExecutionResult(
                    response=final_response,
                    attempts=tuple(attempts),
                )

            except Exception as exc:
                latency_ms = (perf_counter() - started) * 1000.0

                attempts.append(
                    ProviderAttempt(
                        provider=provider_name,
                        success=False,
                        latency_ms=latency_ms,
                        error=str(exc),
                    )
                )

        raise LLMFallbackExecutionError(
            f"all_llm_providers_failed:{len(attempts)}"
        )