# arvis/errors/syscall.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisKernelError,
)


class SyscallExecutionError(ArvisKernelError):
    default_code = "SYSCALL_EXECUTION_ERROR"
    severity = ArvisErrorSeverity.ERROR
    retryable = False


class SyscallValidationError(SyscallExecutionError):
    default_code = "SYSCALL_VALIDATION_ERROR"
    replay_safe = True


class SyscallReplayError(SyscallExecutionError):
    default_code = "SYSCALL_REPLAY_ERROR"
    replay_safe = False


class SyscallExternalDependencyError(SyscallExecutionError):
    default_code = "SYSCALL_EXTERNAL_DEPENDENCY_ERROR"
    retryable = True
    deterministic = False
