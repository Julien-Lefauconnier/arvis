# tests/errors/test_error_factories.py

from arvis.errors.factories import (
    build_llm_fatal_error,
    build_llm_retryable_error,
)


def test_build_llm_retryable_error():
    err = build_llm_retryable_error(
        "retry",
        code="llm_retry",
        retry_class="validation",
    )

    assert err.code == "llm_retry"
    assert err.details["retry_class"] == "validation"
    assert err.domain.value == "llm"


def test_build_llm_fatal_error():
    err = build_llm_fatal_error(
        "fatal",
        code="llm_fatal",
    )

    assert err.code == "llm_fatal"
    assert err.details["retry_class"] == "fatal"
    assert err.domain.value == "llm"
