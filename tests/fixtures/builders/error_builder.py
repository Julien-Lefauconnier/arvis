# tests/fixtures/builders/error_builder.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisError,
    ArvisErrorCategory,
    ArvisErrorSeverity,
)


def build_error(
    *,
    message: str = "error",
    code: str = "TEST_ERROR",
    category: ArvisErrorCategory = ArvisErrorCategory.RUNTIME,
    severity: ArvisErrorSeverity = ArvisErrorSeverity.ERROR,
    retryable: bool = False,
    deterministic: bool = True,
    replay_safe: bool = True,
    degraded: bool = False,
) -> ArvisError:
    # NOTE:
    err = ArvisError(
        message,
        code=code,
    )

    err.category = category
    err.severity = severity
    err.retryable = retryable
    err.deterministic = deterministic
    err.replay_safe = replay_safe
    err.degraded = degraded

    # test-only mutation helper
    # used to emulate future specialized subclasses
    # without generating dozens of synthetic classes

    return err
