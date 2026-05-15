# arvis/errors/runtime_execution.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisRuntimeError,
    ErrorDomain,
    ErrorPolicy,
)
from arvis.errors.codes import ErrorCode


class RuntimeExecutionError(ArvisRuntimeError):
    domain = ErrorDomain.KERNEL
    default_code = ErrorCode.RUNTIME_EXECUTION_ERROR
    severity = ArvisErrorSeverity.ERROR
    policy = ErrorPolicy.FAIL_CLOSED
    replay_safe = False


class ProcessExecutionAborted(RuntimeExecutionError):
    default_code = ErrorCode.PROCESS_EXECUTION_ABORTED
    severity = ArvisErrorSeverity.FATAL
    replay_safe = False


class RuntimeExecutionContractViolation(RuntimeExecutionError):
    default_code = ErrorCode.RUNTIME_EXECUTION_CONTRACT_VIOLATION
    severity = ArvisErrorSeverity.FATAL
    replay_safe = False
