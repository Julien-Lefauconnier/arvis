# arvis/errors/runtime_scheduler.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ErrorDomain,
    ErrorPolicy,
)
from arvis.errors.codes import ErrorCode
from arvis.errors.kernel_runtime import KernelRuntimeError


class SchedulerRuntimeError(KernelRuntimeError):
    domain = ErrorDomain.KERNEL
    default_code = ErrorCode.SCHEDULER_RUNTIME_ERROR
    severity = ArvisErrorSeverity.ERROR
    policy = ErrorPolicy.FAIL_CLOSED
    replay_safe = False


class SchedulerConfigurationError(SchedulerRuntimeError):
    default_code = ErrorCode.SCHEDULER_CONFIGURATION_ERROR


class SchedulerInvariantViolation(SchedulerRuntimeError):
    default_code = ErrorCode.SCHEDULER_INVARIANT_VIOLATION
    severity = ArvisErrorSeverity.FATAL
    replay_safe = False


class InvalidProcessSchedulingError(SchedulerRuntimeError):
    default_code = ErrorCode.INVALID_PROCESS_SCHEDULING


class UnknownProcessError(SchedulerRuntimeError):
    default_code = ErrorCode.UNKNOWN_PROCESS
