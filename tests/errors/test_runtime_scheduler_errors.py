# tests/errors/test_runtime_scheduler_errors.py

from arvis.errors import (
    InvalidProcessSchedulingError,
    SchedulerConfigurationError,
    SchedulerInvariantViolation,
    SchedulerRuntimeError,
    UnknownProcessError,
)
from arvis.errors.base import (
    ArvisErrorSeverity,
    ErrorDomain,
)


def test_scheduler_runtime_error_metadata():
    error = SchedulerRuntimeError("scheduler")

    assert error.domain == ErrorDomain.KERNEL
    assert error.replay_safe is False


def test_scheduler_configuration_error():
    error = SchedulerConfigurationError("config")

    assert error.code == "scheduler_configuration_error"


def test_scheduler_invariant_violation():
    error = SchedulerInvariantViolation("invariant")

    assert error.severity == ArvisErrorSeverity.FATAL


def test_invalid_process_scheduling():
    error = InvalidProcessSchedulingError("invalid")

    assert error.code == "invalid_process_scheduling"


def test_unknown_process_error():
    error = UnknownProcessError("unknown")

    assert error.code == "unknown_process"
