# tests/adapters/llm/test_llm_retry.py

import pytest

from arvis.adapters.llm.runtime.retry import (
    LLMRetryConfig,
    LLMRetryError,
    retry_call,
)


def test_retry_call_returns_on_first_success() -> None:
    calls = 0

    def operation() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    result = retry_call(operation)

    assert result == "ok"
    assert calls == 1


def test_retry_call_succeeds_after_retryable_failures() -> None:
    calls = 0
    sleeps: list[float] = []

    def operation() -> str:
        nonlocal calls
        calls += 1

        if calls < 3:
            raise TimeoutError("temporary timeout")

        return "ok"

    result = retry_call(
        operation,
        config=LLMRetryConfig(
            attempts=3,
            base_delay=0.1,
            max_delay=1.0,
        ),
        sleep_fn=sleeps.append,
    )

    assert result == "ok"
    assert calls == 3
    assert sleeps == [0.1, 0.2]


def test_retry_call_raises_retry_error_after_exhaustion() -> None:
    calls = 0

    def operation() -> str:
        nonlocal calls
        calls += 1
        raise TimeoutError("still failing")

    with pytest.raises(LLMRetryError) as exc_info:
        retry_call(
            operation,
            config=LLMRetryConfig(attempts=3, base_delay=0.0),
        )

    assert calls == 3
    assert isinstance(exc_info.value.__cause__, TimeoutError)


def test_retry_call_does_not_retry_non_retryable_error() -> None:
    calls = 0

    def operation() -> str:
        nonlocal calls
        calls += 1
        raise ValueError("bad request")

    with pytest.raises(ValueError):
        retry_call(
            operation,
            config=LLMRetryConfig(
                attempts=3,
                retry_on=(TimeoutError,),
            ),
        )

    assert calls == 1


def test_retry_call_caps_delay_at_max_delay() -> None:
    sleeps: list[float] = []

    def operation() -> str:
        raise TimeoutError("temporary timeout")

    with pytest.raises(LLMRetryError):
        retry_call(
            operation,
            config=LLMRetryConfig(
                attempts=4,
                base_delay=1.0,
                max_delay=1.5,
            ),
            sleep_fn=sleeps.append,
        )

    assert sleeps == [1.0, 1.5, 1.5]


def test_retry_call_applies_jitter_without_exceeding_max_delay() -> None:
    sleeps: list[float] = []

    def operation() -> str:
        raise TimeoutError("temporary timeout")

    with pytest.raises(LLMRetryError):
        retry_call(
            operation,
            config=LLMRetryConfig(
                attempts=2,
                base_delay=1.0,
                max_delay=1.2,
                jitter=0.5,
            ),
            sleep_fn=sleeps.append,
            random_fn=lambda: 1.0,
        )

    assert sleeps == [1.2]


def test_retry_config_rejects_invalid_attempts() -> None:
    with pytest.raises(ValueError):
        LLMRetryConfig(attempts=0)


def test_retry_config_rejects_negative_delay() -> None:
    with pytest.raises(ValueError):
        LLMRetryConfig(base_delay=-0.1)


def test_retry_config_rejects_negative_jitter() -> None:
    with pytest.raises(ValueError):
        LLMRetryConfig(jitter=-0.1)
