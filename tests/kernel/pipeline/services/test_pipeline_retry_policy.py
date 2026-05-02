# tests/kernel/pipeline/services/test_pipeline_retry_policy.py

from __future__ import annotations

import pytest

from arvis.kernel.pipeline.services.pipeline_retry_policy import PipelineRetryPolicy
from arvis.kernel_core.syscalls.errors import SyscallError


def test_retry_policy_does_not_retry_without_error_detail() -> None:
    policy = PipelineRetryPolicy(max_attempts=3)

    decision = policy.decide(
        error=None,
        attempt=0,
    )

    assert decision.should_retry is False
    assert decision.reason == "no_error_detail"


def test_retry_policy_does_not_retry_non_retryable_error() -> None:
    policy = PipelineRetryPolicy(max_attempts=3)

    decision = policy.decide(
        error=SyscallError(
            code="no_llm_adapter",
            message="missing adapter",
            retryable=False,
        ),
        attempt=0,
    )

    assert decision.should_retry is False
    assert decision.reason == "not_retryable"


def test_retry_policy_retries_retryable_error_before_limit() -> None:
    policy = PipelineRetryPolicy(max_attempts=3)

    decision = policy.decide(
        error=SyscallError(
            code="llm_execution_failed",
            message="temporary",
            retryable=True,
        ),
        attempt=0,
    )

    assert decision.should_retry is True
    assert decision.reason == "retryable"
    assert decision.next_attempt == 1


def test_retry_policy_stops_at_attempt_limit() -> None:
    policy = PipelineRetryPolicy(max_attempts=2)

    decision = policy.decide(
        error=SyscallError(
            code="llm_execution_failed",
            message="temporary",
            retryable=True,
        ),
        attempt=1,
    )

    assert decision.should_retry is False
    assert decision.reason == "attempt_limit_reached"


def test_retry_policy_computes_exponential_delay() -> None:
    policy = PipelineRetryPolicy(
        max_attempts=4,
        base_delay_ms=100,
        max_delay_ms=1_000,
    )

    decision = policy.decide(
        error=SyscallError(
            code="llm_execution_failed",
            message="temporary",
            retryable=True,
        ),
        attempt=2,
    )

    assert decision.should_retry is True
    assert decision.delay_ms == 400


def test_retry_policy_caps_delay() -> None:
    policy = PipelineRetryPolicy(
        max_attempts=5,
        base_delay_ms=500,
        max_delay_ms=1_000,
    )

    decision = policy.decide(
        error=SyscallError(
            code="llm_execution_failed",
            message="temporary",
            retryable=True,
        ),
        attempt=3,
    )

    assert decision.should_retry is True
    assert decision.delay_ms == 1_000


def test_retry_policy_respects_retry_class_permanent() -> None:
    policy = PipelineRetryPolicy(max_attempts=3)

    error = SyscallError(
        code="x",
        message="fail",
        retryable=True,
        metadata={"retry_class": "permanent"},
    )

    decision = policy.decide(error=error, attempt=0)

    assert decision.should_retry is False


def test_retry_policy_rate_limit_backoff_stronger() -> None:
    policy = PipelineRetryPolicy(
        max_attempts=3,
        base_delay_ms=100,
    )

    error = SyscallError(
        code="x",
        message="rate limited",
        retryable=True,
        metadata={"retry_class": "rate_limit"},
    )

    d1 = policy.decide(error=error, attempt=0)
    d2 = policy.decide(error=error, attempt=1)

    assert d2.delay_ms > d1.delay_ms
    assert d2.retry_class == "rate_limit"


def test_retry_policy_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError):
        PipelineRetryPolicy(max_attempts=0)

    with pytest.raises(ValueError):
        PipelineRetryPolicy(base_delay_ms=-1)

    with pytest.raises(ValueError):
        PipelineRetryPolicy(max_delay_ms=-1)


def test_retry_policy_without_jitter_is_deterministic() -> None:
    policy = PipelineRetryPolicy(
        max_attempts=3,
        base_delay_ms=100,
    )

    decision = policy.decide(
        error=SyscallError(
            code="llm_execution_failed",
            message="temporary",
            retryable=True,
        ),
        attempt=1,
    )

    # base_delay * 2^1 = 200
    assert decision.delay_ms == 200


def test_retry_policy_rng_jitter_is_bounded() -> None:
    import random

    policy = PipelineRetryPolicy(
        max_attempts=3,
        base_delay_ms=100,
        rng=random.Random(42),
    )

    decision = policy.decide(
        error=SyscallError(
            code="x",
            message="temporary",
            retryable=True,
        ),
        attempt=1,
    )

    assert 0 <= decision.delay_ms <= 200


def test_retry_policy_jitter_fn_is_clamped() -> None:
    policy = PipelineRetryPolicy(
        max_attempts=3,
        base_delay_ms=100,
        jitter_fn=lambda delay: delay * 10,  # dépassement volontaire
    )

    decision = policy.decide(
        error=SyscallError(
            code="x",
            message="temporary",
            retryable=True,
        ),
        attempt=1,
    )

    # delay normal = 200
    assert decision.delay_ms == 200


def test_retry_policy_uses_injected_jitter_fn() -> None:
    policy = PipelineRetryPolicy(
        max_attempts=3,
        base_delay_ms=100,
        jitter_fn=lambda delay: delay // 2,
    )

    decision = policy.decide(
        error=SyscallError(
            code="llm_execution_failed",
            message="temporary",
            retryable=True,
        ),
        attempt=1,
    )

    assert decision.delay_ms == 100


def test_retry_policy_jitter_is_bounded() -> None:
    policy = PipelineRetryPolicy(
        max_attempts=3,
        base_delay_ms=100,
    )

    decision = policy.decide(
        error=SyscallError(
            code="llm_execution_failed",
            message="temporary",
            retryable=True,
        ),
        attempt=1,
    )

    assert 0 <= decision.delay_ms <= 200
