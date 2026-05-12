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
