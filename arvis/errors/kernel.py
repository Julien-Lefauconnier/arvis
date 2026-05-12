# arvis/errors/kernel.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisKernelError,
    ErrorDomain,
    ErrorPolicy,
)


class KernelInvariantViolation(ArvisKernelError):
    domain = ErrorDomain.KERNEL
    default_code = "KERNEL_INVARIANT_VIOLATION"
    severity = ArvisErrorSeverity.FATAL
    policy = ErrorPolicy.FAIL_CLOSED
    replay_safe = False


class KernelFailClosedError(ArvisKernelError):
    domain = ErrorDomain.KERNEL
    default_code = "KERNEL_FAIL_CLOSED"
    severity = ArvisErrorSeverity.ERROR
    replay_safe = True


class KernelDegradedWarning(ArvisKernelError):
    domain = ErrorDomain.KERNEL
    default_code = "KERNEL_DEGRADED_WARNING"
    severity = ArvisErrorSeverity.WARNING
    policy = ErrorPolicy.DEGRADE
    degraded = True
