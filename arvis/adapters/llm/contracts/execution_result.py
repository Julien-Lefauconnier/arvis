# arvis/adapters/llm/contracts/execution_result.py

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.errors.base import ArvisError


@dataclass(frozen=True, slots=True)
class ProviderAttempt:
    provider: str
    success: bool
    latency_ms: float
    error: str | None = None


class LLMExecutionStatus(StrEnum):
    SUCCESS = "success"
    ABSTAINED = "abstained"
    RETRY_EXHAUSTED = "retry_exhausted"
    FALLBACK_USED = "fallback_used"
    VALIDATION_FAILED = "validation_failed"
    PROVIDER_FAILURE = "provider_failure"
    DEGRADED = "degraded"


@dataclass(frozen=True, slots=True)
class LLMExecutionResult:
    status: LLMExecutionStatus

    response: LLMResponse | None

    retry_count: int
    fallback_used: bool

    provider_attempts: tuple[ProviderAttempt, ...]

    evaluation: dict[str, object]
    observation: dict[str, object]

    error: ArvisError | None

    degraded: bool
    replay_safe: bool

    require_confirmation: bool
