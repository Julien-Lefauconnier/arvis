# arvis/errors/kernel.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisKernelError,
)


class KernelInvariantViolation(ArvisKernelError):
    default_code = "KERNEL_INVARIANT_VIOLATION"
    severity = ArvisErrorSeverity.FATAL
    replay_safe = False


class KernelFailClosedError(ArvisKernelError):
    default_code = "KERNEL_FAIL_CLOSED"
    severity = ArvisErrorSeverity.ERROR
    replay_safe = True


class KernelDegradedWarning(ArvisKernelError):
    default_code = "KERNEL_DEGRADED_WARNING"
    severity = ArvisErrorSeverity.WARNING
    degraded = True
