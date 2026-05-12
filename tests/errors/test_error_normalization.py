# tests/errors/test_error_normalization.py

from __future__ import annotations

from arvis.errors.base import ArvisError, ArvisExternalError, ArvisRuntimeError
from arvis.errors.normalization import normalize_error


def test_normalize_arvis_error_passthrough():
    error = ArvisRuntimeError("boom")

    assert normalize_error(error) is error


def test_normalize_unknown_exception_as_runtime_error():
    error = normalize_error(ValueError("invalid"))

    assert isinstance(error, ArvisRuntimeError)
    assert error.details["exception_type"] == "ValueError"


def test_normalize_timeout_as_external_error():
    error = normalize_error(TimeoutError("timeout"))

    assert isinstance(error, ArvisExternalError)
    assert error.retryable is True
    assert error.deterministic is False


def test_normalize_returns_arvis_error():
    error = normalize_error(Exception("boom"))

    assert isinstance(error, ArvisError)
