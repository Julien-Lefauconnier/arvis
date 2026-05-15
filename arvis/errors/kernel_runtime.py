# arvis/errors/kernel_runtime.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisKernelError,
    ErrorDomain,
    ErrorPolicy,
)
from arvis.errors.codes import ErrorCode


class KernelRuntimeError(ArvisKernelError):
    domain = ErrorDomain.KERNEL
    default_code = ErrorCode.KERNEL_RUNTIME_ERROR
    severity = ArvisErrorSeverity.ERROR
    policy = ErrorPolicy.FAIL_CLOSED
    replay_safe = False


class SyscallRegistryError(KernelRuntimeError):
    default_code = ErrorCode.SYSCALL_REGISTRY_ERROR


class DuplicateSyscallRegistrationError(SyscallRegistryError):
    default_code = ErrorCode.DUPLICATE_SYSCALL_REGISTRATION
