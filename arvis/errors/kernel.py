# arvis/errors/kernel.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisKernelError,
    ErrorDomain,
    ErrorPolicy,
)
from arvis.errors.codes import ErrorCode


class KernelInvariantViolation(ArvisKernelError):
    domain = ErrorDomain.KERNEL
    default_code = ErrorCode.KERNEL_INVARIANT_VIOLATION
    severity = ArvisErrorSeverity.FATAL
    policy = ErrorPolicy.FAIL_CLOSED
    replay_safe = False


class KernelFailClosedError(ArvisKernelError):
    domain = ErrorDomain.KERNEL
    default_code = ErrorCode.KERNEL_FAIL_CLOSED
    severity = ArvisErrorSeverity.ERROR
    replay_safe = True


class KernelDegradedWarning(ArvisKernelError):
    domain = ErrorDomain.KERNEL
    default_code = ErrorCode.KERNEL_DEGRADED_WARNING
    severity = ArvisErrorSeverity.WARNING
    policy = ErrorPolicy.DEGRADE
    degraded = True
