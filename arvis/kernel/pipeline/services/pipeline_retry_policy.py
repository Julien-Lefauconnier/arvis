# arvis/kernel/pipeline/services/pipeline_retry_policy.py

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, cast

from arvis.kernel_core.syscalls.errors import SyscallError

RetryDecisionReason = Literal[
    "success",
    "no_error_detail",
    "not_retryable",
    "attempt_limit_reached",
    "retryable",
]

RetryClass = Literal[
    "transient",
    "rate_limit",
    "permanent",
    "unknown",
]


@dataclass(frozen=True, slots=True)
class PipelineRetryDecision:
    should_retry: bool
    reason: RetryDecisionReason
    next_attempt: int
    delay_ms: int = 0
    retry_class: RetryClass = "unknown"


@dataclass(frozen=True, slots=True)
class PipelineRetryPolicy:
    max_attempts: int = 1
    base_delay_ms: int = 0
    max_delay_ms: int = 0
    jitter_fn: Callable[[int], int] | None = None
    rng: random.Random | None = None

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")

        if self.base_delay_ms < 0:
            raise ValueError("base_delay_ms must be >= 0")

        if self.max_delay_ms < 0:
            raise ValueError("max_delay_ms must be >= 0")

    def decide(
        self,
        *,
        error: SyscallError | None,
        attempt: int,
    ) -> PipelineRetryDecision:
        if error is None:
            return PipelineRetryDecision(
                should_retry=False,
                reason="no_error_detail",
                next_attempt=attempt,
            )

        retry_class = self._extract_retry_class(error)

        if not error.retryable or retry_class == "permanent":
            return PipelineRetryDecision(
                should_retry=False,
                reason="not_retryable",
                next_attempt=attempt,
                retry_class=retry_class,
            )

        if attempt + 1 >= self.max_attempts:
            return PipelineRetryDecision(
                should_retry=False,
                reason="attempt_limit_reached",
                next_attempt=attempt,
                retry_class=retry_class,
            )

        return PipelineRetryDecision(
            should_retry=True,
            reason="retryable",
            next_attempt=attempt + 1,
            delay_ms=self._compute_delay_ms(attempt, retry_class),
            retry_class=retry_class,
        )

    def _compute_delay_ms(self, attempt: int, retry_class: RetryClass) -> int:
        if self.base_delay_ms <= 0:
            return 0

        multiplier = 2
        if retry_class == "rate_limit":
            multiplier = 4

        delay: int = self.base_delay_ms * (multiplier**attempt)

        if self.max_delay_ms > 0:
            delay = min(delay, self.max_delay_ms)

        # --- JITTER RESOLUTION (clean & deterministic) ---

        if self.jitter_fn is not None:
            jittered = self.jitter_fn(delay)
            return max(0, min(jittered, delay))

        if self.rng is not None:
            return self.rng.randint(0, delay)

        return delay

    def _extract_retry_class(self, error: SyscallError) -> RetryClass:
        metadata = error.metadata or {}
        value = metadata.get("retry_class")

        if value in {"transient", "rate_limit", "permanent"}:
            return cast(RetryClass, value)

        return "unknown"
