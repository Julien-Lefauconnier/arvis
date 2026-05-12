# arvis/errors/__init__.py

from arvis.errors.api import (
    ArvisAPIError,
    CognitiveStateRequiredError,
    InvalidIRPayloadError,
)
from arvis.errors.base import (
    ArvisDegradedModeError,
    ArvisDomainError,
    ArvisError,
    ArvisErrorCategory,
    ArvisErrorMetadata,
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
from arvis.errors.replay import (
    ReplayCognitiveStateMissing,
    ReplayGlobalCommitmentMismatch,
    ReplayGlobalCommitmentMissing,
    ReplayVerificationError,
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
    "ArvisErrorMetadata",
    "ArvisInvariantViolation",
    "ArvisRuntimeError",
    "ArvisDomainError",
    "ArvisExternalError",
    "ArvisAPIError",
    "CognitiveStateRequiredError",
    "InvalidIRPayloadError",
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
    "ReplayVerificationError",
    "ReplayGlobalCommitmentMissing",
    "ReplayGlobalCommitmentMismatch",
    "ReplayCognitiveStateMissing",
    "SyscallExecutionError",
    "SyscallValidationError",
    "SyscallReplayError",
    "SyscallExternalDependencyError",
]
