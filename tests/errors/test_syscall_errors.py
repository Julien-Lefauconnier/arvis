# tests/errors/test_syscall_errors.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorCategory,
    ArvisErrorSeverity,
    ErrorDomain,
    ErrorPolicy,
    ErrorSemantics,
)
from arvis.errors.syscall import (
    SyscallExecutionError,
    SyscallExternalDependencyError,
    SyscallReplayError,
    SyscallValidationError,
)


def test_syscall_execution_error():
    error = SyscallExecutionError("execution")

    assert error.category == ArvisErrorCategory.KERNEL
    assert error.domain == ErrorDomain.SYSCALL
    assert error.severity == ArvisErrorSeverity.ERROR
    assert error.policy == ErrorPolicy.FAIL_CLOSED
    assert error.retryable is False


def test_syscall_validation_error():
    error = SyscallValidationError("validation")

    assert error.policy == ErrorPolicy.FAIL_CLOSED
    assert error.replay_safe is True


def test_syscall_replay_error():
    error = SyscallReplayError("replay")

    assert error.replay_safe is False


def test_syscall_external_dependency_error():
    error = SyscallExternalDependencyError("external")

    assert error.policy == ErrorPolicy.RETRY
    assert error.retryable is True
    assert error.deterministic is False

    semantics = {s.value for s in error.metadata.semantics}

    assert ErrorSemantics.TRANSIENT.value in semantics
    assert ErrorSemantics.NON_DETERMINISTIC.value in semantics
