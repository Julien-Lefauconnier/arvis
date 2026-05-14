# tests/fixtures/errors.py

from __future__ import annotations

import pytest

from arvis.errors.base import (
    ArvisDegradedModeError,
    ArvisError,
    ArvisExternalError,
    ArvisInvariantViolation,
)
from tests.fixtures.builders.error_builder import build_error


@pytest.fixture
def runtime_error() -> ArvisError:
    return build_error()


@pytest.fixture
def invariant_error() -> ArvisInvariantViolation:
    return ArvisInvariantViolation(
        "invariant violation",
        code="INVARIANT_VIOLATION",
    )


@pytest.fixture
def degraded_error() -> ArvisDegradedModeError:
    return ArvisDegradedModeError(
        "degraded mode",
        code="DEGRADED_MODE",
    )


@pytest.fixture
def external_error() -> ArvisExternalError:
    return ArvisExternalError(
        "external failure",
        code="EXTERNAL_FAILURE",
    )


@pytest.fixture
def retryable_external_error() -> ArvisExternalError:
    return ArvisExternalError(
        "transient external failure",
        code="TRANSIENT_EXTERNAL_FAILURE",
        details={
            "retry_class": "transient",
        },
    )


@pytest.fixture
def permanent_external_error() -> ArvisExternalError:
    return ArvisExternalError(
        "permanent external failure",
        code="PERMANENT_EXTERNAL_FAILURE",
        details={
            "retry_class": "permanent",
        },
    )


@pytest.fixture
def rate_limit_external_error() -> ArvisExternalError:
    return ArvisExternalError(
        "rate limited",
        code="RATE_LIMITED",
        details={
            "retry_class": "rate_limit",
        },
    )
