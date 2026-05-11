# arvis/errors/__init__.py

from arvis.errors.base import (
    ArvisDegradedModeError,
    ArvisDomainError,
    ArvisError,
    ArvisErrorCategory,
    ArvisErrorSeverity,
    ArvisExternalError,
    ArvisInvariantViolation,
    ArvisKernelError,
    ArvisReplayError,
    ArvisRuntimeError,
    ArvisSecurityError,
)
from arvis.errors.helpers import append_error
from arvis.errors.kernel import (
    KernelDegradedWarning,
    KernelFailClosedError,
    KernelInvariantViolation,
)
from arvis.errors.pipeline import (
    PipelineFailClosedError,
    PipelineStageDegradedError,
    PipelineStageError,
)
from arvis.errors.syscall import (
    SyscallExecutionError,
    SyscallExternalDependencyError,
    SyscallReplayError,
    SyscallValidationError,
)

__all__ = [
    "ArvisError",
    "ArvisErrorCategory",
    "ArvisErrorSeverity",
    "ArvisInvariantViolation",
    "ArvisRuntimeError",
    "ArvisDomainError",
    "ArvisExternalError",
    "ArvisReplayError",
    "ArvisSecurityError",
    "ArvisKernelError",
    "ArvisDegradedModeError",
    "append_error",
    "KernelInvariantViolation",
    "KernelFailClosedError",
    "KernelDegradedWarning",
    "PipelineStageError",
    "PipelineStageDegradedError",
    "PipelineFailClosedError",
    "SyscallExecutionError",
    "SyscallValidationError",
    "SyscallReplayError",
    "SyscallExternalDependencyError",
]
