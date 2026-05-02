# tests/kernel_core/syscall/test_syscall_errors.py

from __future__ import annotations

from arvis.kernel_core.syscalls.errors import SyscallError
from arvis.kernel_core.syscalls.syscall import SyscallResult


def test_syscall_error_legacy_string() -> None:
    error = SyscallError(
        code="unknown_syscall",
        message="missing.call",
    )

    assert error.to_legacy_string() == "unknown_syscall:missing.call"


def test_syscall_result_failure_keeps_legacy_and_structured_error() -> None:
    error = SyscallError(
        code="llm_failed",
        message="provider unavailable",
        retryable=True,
    )

    result = SyscallResult.failure(error)

    assert result.success is False
    assert result.error == "llm_failed:provider unavailable"
    assert result.error_detail is error
    assert result.error_detail.to_dict()["retryable"] is True
