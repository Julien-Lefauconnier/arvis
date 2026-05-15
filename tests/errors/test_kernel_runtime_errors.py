# tests/errors/test_kernel_runtime_errors.py

from __future__ import annotations

from arvis.errors import (
    ArvisErrorCategory,
    ArvisErrorSeverity,
    DuplicateSyscallRegistrationError,
    ErrorCode,
    ErrorDomain,
    ErrorPolicy,
    KernelRuntimeError,
    SyscallRegistryError,
)


def test_kernel_runtime_error_defaults() -> None:
    err = KernelRuntimeError("runtime failure")

    assert err.code == ErrorCode.KERNEL_RUNTIME_ERROR
    assert err.domain == ErrorDomain.KERNEL
    assert err.category == ArvisErrorCategory.KERNEL
    assert err.policy == ErrorPolicy.FAIL_CLOSED
    assert err.severity == ArvisErrorSeverity.ERROR
    assert err.replay_safe is False


def test_syscall_registry_error_defaults() -> None:
    err = SyscallRegistryError("registry failure")

    assert err.code == ErrorCode.SYSCALL_REGISTRY_ERROR


def test_duplicate_syscall_registration_error_defaults() -> None:
    err = DuplicateSyscallRegistrationError("duplicate syscall")

    assert err.code == ErrorCode.DUPLICATE_SYSCALL_REGISTRATION
