# tests/errors/test_error_contracts.py

from __future__ import annotations

import inspect

import arvis.errors as errors_pkg
from arvis.errors.base import ArvisError


def iter_error_classes():
    for _, obj in inspect.getmembers(errors_pkg):
        if (
            inspect.isclass(obj)
            and issubclass(obj, ArvisError)
            and obj is not ArvisError
        ):
            yield obj


def test_all_errors_are_serializable():
    for error_cls in iter_error_classes():
        error = error_cls("test")

        payload = error.to_dict()

        assert isinstance(payload, dict)
        assert "code" in payload
        assert "domain" in payload
        assert "category" in payload
        assert "severity" in payload
        assert "policy" in payload
        assert "semantics" in payload
        assert "message" in payload
        assert "type" in payload


def test_all_errors_have_valid_metadata():
    for error_cls in iter_error_classes():
        error = error_cls("test")

        metadata = error.metadata

        assert metadata.code
        assert metadata.domain
        assert metadata.category
        assert metadata.severity
        assert metadata.policy


def test_fatal_errors_are_not_retryable():
    for error_cls in iter_error_classes():
        error = error_cls("test")

        if error.severity.value == "fatal":
            assert error.retryable is False


def test_degraded_errors_have_warning_or_info():
    for error_cls in iter_error_classes():
        error = error_cls("test")

        if error.degraded:
            assert error.severity.value in {
                "warning",
                "info",
            }


def test_retryable_errors_have_retry_policy():
    for error_cls in iter_error_classes():
        error = error_cls("test")

        if error.retryable:
            assert error.metadata.policy.value in {
                "retry",
                "degrade",
            }


def test_non_deterministic_errors_have_semantic_flag():
    for error_cls in iter_error_classes():
        error = error_cls("test")

        if not error.deterministic:
            semantics = {s.value for s in error.metadata.semantics}

            assert "non_deterministic" in semantics
