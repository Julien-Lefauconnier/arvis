# tests/errors/test_kernel_errors.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorCategory,
    ArvisErrorSeverity,
)
from arvis.errors.kernel import (
    KernelDegradedWarning,
    KernelFailClosedError,
    KernelInvariantViolation,
)


def test_kernel_invariant_violation():
    error = KernelInvariantViolation("kernel invariant")

    assert error.category == ArvisErrorCategory.KERNEL
    assert error.severity == ArvisErrorSeverity.FATAL
    assert error.replay_safe is False


def test_kernel_fail_closed_error():
    error = KernelFailClosedError("fail closed")

    assert error.category == ArvisErrorCategory.KERNEL
    assert error.severity == ArvisErrorSeverity.ERROR
    assert error.replay_safe is True


def test_kernel_degraded_warning():
    error = KernelDegradedWarning("degraded")

    assert error.category == ArvisErrorCategory.KERNEL
    assert error.severity == ArvisErrorSeverity.WARNING
    assert error.degraded is True
