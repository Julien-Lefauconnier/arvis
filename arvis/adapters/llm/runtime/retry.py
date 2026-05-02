# arvis/adapters/llm/runtime/retry.py

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
from typing import TypeVar

T = TypeVar("T")


class LLMRetryError(RuntimeError):
    """Raised when a retryable operation exhausts all retry attempts."""


@dataclass(frozen=True, slots=True)
class LLMRetryConfig:
    attempts: int = 3
    base_delay: float = 0.25
    max_delay: float = 2.0
    jitter: float = 0.0
    retry_on: tuple[type[Exception], ...] = (
        TimeoutError,
        ConnectionError,
    )

    def __post_init__(self) -> None:
        if self.attempts <= 0:
            raise ValueError("LLMRetryConfig.attempts must be > 0")
        if self.base_delay < 0:
            raise ValueError("LLMRetryConfig.base_delay must be >= 0")
        if self.max_delay < 0:
            raise ValueError("LLMRetryConfig.max_delay must be >= 0")
        if self.jitter < 0:
            raise ValueError("LLMRetryConfig.jitter must be >= 0")


def retry_call(
    operation: Callable[[], T],
    *,
    config: LLMRetryConfig | None = None,
    sleep_fn: Callable[[float], None] = sleep,
    random_fn: Callable[[], float] = random.random,
) -> T:
    active_config = config or LLMRetryConfig()
    last_error: Exception | None = None

    for attempt_index in range(active_config.attempts):
        try:
            return operation()
        except active_config.retry_on as exc:
            last_error = exc

            is_last_attempt = attempt_index == active_config.attempts - 1
            if is_last_attempt:
                break

            delay = _compute_delay(
                attempt_index=attempt_index,
                base_delay=active_config.base_delay,
                max_delay=active_config.max_delay,
                jitter=active_config.jitter,
                random_fn=random_fn,
            )

            if delay > 0:
                sleep_fn(delay)

    raise LLMRetryError("LLM operation failed after retry exhaustion") from last_error


def _compute_delay(
    *,
    attempt_index: int,
    base_delay: float,
    max_delay: float,
    jitter: float,
    random_fn: Callable[[], float],
) -> float:
    exponential_delay: float = base_delay * float(2**attempt_index)
    bounded_delay: float = (
        exponential_delay if exponential_delay < max_delay else max_delay
    )

    if jitter <= 0:
        return float(bounded_delay)

    jitter_amount: float = jitter * random_fn()
    delayed: float = bounded_delay + jitter_amount

    return float(delayed if delayed < max_delay else max_delay)
