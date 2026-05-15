# arvis/errors/__init__.py

from arvis.errors.api import (
    ArvisAPIError,
    CognitiveStateRequiredError,
    InvalidIRPayloadError,
)
from arvis.errors.artifact import (
    ArtifactConsistencyError,
    ArtifactError,
    ArtifactInvalidStatusError,
    ArtifactTimestampMissingError,
    ArtifactValidationError,
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
    ErrorDomain,
    ErrorPolicy,
    ErrorSemantics,
)
from arvis.errors.codes import ErrorCode
from arvis.errors.context import ErrorContextLike, ensure_error_extra, has_error_extra
from arvis.errors.disposition import ErrorDisposition, disposition_from_policy
from arvis.errors.helpers import append_error
from arvis.errors.kernel import (
    KernelDegradedWarning,
    KernelFailClosedError,
    KernelInvariantViolation,
)
from arvis.errors.kernel_runtime import (
    DuplicateSyscallRegistrationError,
    KernelRuntimeError,
    SyscallRegistryError,
)
from arvis.errors.llm_runtime import (
    LLMEmptyResponseError,
    LLMExecutionContractViolation,
    LLMFallbackExhaustedError,
    LLMRetryExhaustedError,
    LLMRuntimeError,
)
from arvis.errors.manager import ErrorManager
from arvis.errors.normalization import normalize_error
from arvis.errors.pipeline import (
    PipelineFailClosedError,
    PipelineStageDegradedError,
    PipelineStageError,
)
from arvis.errors.policy import ErrorPolicyDecision, decide_error_policy
from arvis.errors.provenance import (
    ErrorCause,
    ErrorOrigin,
    build_error_fingerprint,
    cause_from_exception,
)
from arvis.errors.redaction import redact_error_payload
from arvis.errors.registry import error_code_registry, iter_error_classes
from arvis.errors.replay import (
    ReplayCognitiveStateMissing,
    ReplayGlobalCommitmentMismatch,
    ReplayGlobalCommitmentMissing,
    ReplayVerificationError,
)
from arvis.errors.runtime import (
    AdaptiveComputationError,
    CompositeComputationError,
    ProjectionComputationError,
    RuntimeDegradationError,
    StabilityEvaluationError,
)
from arvis.errors.runtime_execution import (
    ProcessExecutionAborted,
    RuntimeExecutionContractViolation,
    RuntimeExecutionError,
)
from arvis.errors.runtime_pipeline import (
    PipelineExecutionContractViolation,
    PipelineRuntimeError,
)
from arvis.errors.runtime_scheduler import (
    InvalidProcessSchedulingError,
    SchedulerConfigurationError,
    SchedulerInvariantViolation,
    SchedulerRuntimeError,
    UnknownProcessError,
)
from arvis.errors.syscall import (
    SyscallExecutionError,
    SyscallExternalDependencyError,
    SyscallReplayError,
    SyscallValidationError,
)
from arvis.errors.tool_runtime import (
    ToolAuthorizationError,
    ToolExecutionError,
    UnknownToolError,
)

__all__ = [
    "ArvisError",
    "ArvisErrorCategory",
    "ArvisErrorSeverity",
    "ErrorDomain",
    "ErrorSemantics",
    "ErrorPolicy",
    "ArvisErrorMetadata",
    "ArvisInvariantViolation",
    "ArvisRuntimeError",
    "ArvisDomainError",
    "ArvisExternalError",
    "ArvisAPIError",
    "CognitiveStateRequiredError",
    "RuntimeDegradationError",
    "CompositeComputationError",
    "AdaptiveComputationError",
    "ProjectionComputationError",
    "StabilityEvaluationError",
    "InvalidIRPayloadError",
    "ErrorManager",
    "ErrorCode",
    "ErrorDisposition",
    "disposition_from_policy",
    "ErrorContextLike",
    "ensure_error_extra",
    "has_error_extra",
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
    "normalize_error",
    "ErrorPolicyDecision",
    "decide_error_policy",
    "redact_error_payload",
    "ErrorOrigin",
    "ErrorCause",
    "build_error_fingerprint",
    "cause_from_exception",
    "iter_error_classes",
    "error_code_registry",
    "ReplayGlobalCommitmentMissing",
    "ReplayGlobalCommitmentMismatch",
    "ReplayCognitiveStateMissing",
    "SyscallExecutionError",
    "SyscallValidationError",
    "SyscallReplayError",
    "SyscallExternalDependencyError",
    "ArtifactError",
    "ArtifactValidationError",
    "ArtifactTimestampMissingError",
    "ArtifactInvalidStatusError",
    "ArtifactConsistencyError",
    "KernelRuntimeError",
    "SyscallRegistryError",
    "DuplicateSyscallRegistrationError",
    "SchedulerRuntimeError",
    "SchedulerConfigurationError",
    "SchedulerInvariantViolation",
    "InvalidProcessSchedulingError",
    "UnknownProcessError",
    "PipelineRuntimeError",
    "PipelineExecutionContractViolation",
    "ProcessExecutionAborted",
    "RuntimeExecutionContractViolation",
    "RuntimeExecutionError",
    "ToolAuthorizationError",
    "ToolExecutionError",
    "UnknownToolError",
    "LLMEmptyResponseError",
    "LLMExecutionContractViolation",
    "LLMFallbackExhaustedError",
    "LLMRetryExhaustedError",
    "LLMRuntimeError",
]
