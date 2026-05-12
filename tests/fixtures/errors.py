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
    err = ArvisInvariantViolation("invariant violation")

    err.code = "INVARIANT_VIOLATION"

    return err


@pytest.fixture
def degraded_error() -> ArvisDegradedModeError:
    err = ArvisDegradedModeError("degraded mode")

    err.code = "DEGRADED_MODE"

    return err


@pytest.fixture
def external_error() -> ArvisExternalError:
    err = ArvisExternalError("external failure")

    err.code = "EXTERNAL_FAILURE"

    return err
