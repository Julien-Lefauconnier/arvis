# arvis/errors/syscall.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisKernelError,
)


class SyscallExecutionError(ArvisKernelError):
    severity = ArvisErrorSeverity.ERROR
    retryable = False


class SyscallValidationError(SyscallExecutionError):
    replay_safe = True


class SyscallReplayError(SyscallExecutionError):
    replay_safe = False


class SyscallExternalDependencyError(SyscallExecutionError):
    retryable = True
    deterministic = False
