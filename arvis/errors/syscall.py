# arvis/errors/syscall.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisKernelError,
    ErrorDomain,
    ErrorPolicy,
)
from arvis.errors.codes import ErrorCode


class SyscallExecutionError(ArvisKernelError):
    domain = ErrorDomain.SYSCALL
    default_code = ErrorCode.SYSCALL_EXECUTION_ERROR
    severity = ArvisErrorSeverity.ERROR
    retryable = False


class SyscallValidationError(SyscallExecutionError):
    default_code = ErrorCode.SYSCALL_VALIDATION_ERROR
    replay_safe = True
    policy = ErrorPolicy.FAIL_CLOSED


class SyscallReplayError(SyscallExecutionError):
    default_code = ErrorCode.SYSCALL_REPLAY_ERROR
    replay_safe = False


class SyscallExternalDependencyError(SyscallExecutionError):
    default_code = ErrorCode.SYSCALL_EXTERNAL_DEPENDENCY_ERROR
    retryable = True
    deterministic = False
    policy = ErrorPolicy.RETRY
