# arvis/errors/kernel.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisKernelError,
)


class KernelInvariantViolation(ArvisKernelError):
    severity = ArvisErrorSeverity.FATAL
    replay_safe = False


class KernelFailClosedError(ArvisKernelError):
    severity = ArvisErrorSeverity.ERROR
    replay_safe = True


class KernelDegradedWarning(ArvisKernelError):
    severity = ArvisErrorSeverity.WARNING
    degraded = True
