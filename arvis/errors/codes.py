# arvis/errors/codes.py

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    # =========================================================
    # Generic
    # =========================================================

    ARVIS_ERROR = "arvis_error"
    RUNTIME_ERROR = "runtime_error"
    DOMAIN_ERROR = "domain_error"
    EXTERNAL_ERROR = "external_error"
    INVARIANT_VIOLATION = "invariant_violation"
    DEGRADED_MODE = "degraded_mode"

    # =========================================================
    # API
    # =========================================================

    API_ERROR = "api_error"
    COGNITIVE_STATE_REQUIRED = "cognitive_state_required"
    INVALID_IR_PAYLOAD = "invalid_ir_payload"

    # =========================================================
    # Pipeline
    # =========================================================

    PIPELINE_STAGE_FAILURE = "pipeline_stage_failure"
    PIPELINE_STAGE_ERROR = "pipeline_stage_error"
    PIPELINE_STAGE_DEGRADED = "pipeline_stage_degraded"
    PIPELINE_FAIL_CLOSED = "pipeline_fail_closed"

    # =========================================================
    # Runtime
    # =========================================================

    RUNTIME_DEGRADATION = "runtime_degradation"

    # =========================================================
    # Computation
    # =========================================================

    COMPUTATION_FAILURE = "computation_failure"
    PROJECTION_COMPUTATION_ERROR = "projection_computation_error"
    COMPOSITE_COMPUTATION_ERROR = "composite_computation_error"
    ADAPTIVE_COMPUTATION_ERROR = "adaptive_computation_error"
    STABILITY_EVALUATION_ERROR = "stability_evaluation_error"

    # =========================================================
    # Kernel
    # =========================================================

    KERNEL_ERROR = "kernel_error"
    KERNEL_FAIL_CLOSED = "kernel_fail_closed"
    KERNEL_INVARIANT_VIOLATION = "kernel_invariant_violation"
    KERNEL_DEGRADED_WARNING = "kernel_degraded_warning"

    # =========================================================
    # Replay
    # =========================================================

    REPLAY_ERROR = "replay_error"
    SECURITY_ERROR = "security_error"
    REPLAY_VERIFICATION_FAILED = "replay_verification_failed"
    REPLAY_GLOBAL_COMMITMENT_MISSING = "replay_global_commitment_missing"
    REPLAY_GLOBAL_COMMITMENT_MISMATCH = "replay_global_commitment_mismatch"
    REPLAY_COGNITIVE_STATE_MISSING = "replay_cognitive_state_missing"

    # =========================================================
    # Syscalls
    # =========================================================

    SYSCALL_EXECUTION_ERROR = "syscall_execution_error"
    UNKNOWN_SYSCALL = "unknown_syscall"
    INVALID_SYSCALL_ARGS = "invalid_syscall_args"
    INVALID_SYSCALL_RETURN_TYPE = "invalid_syscall_return_type"
    SYSCALL_VALIDATION_ERROR = "syscall_validation_error"
    SYSCALL_REPLAY_ERROR = "syscall_replay_error"
    SYSCALL_EXTERNAL_DEPENDENCY_ERROR = "syscall_external_dependency_error"

    # =========================================================
    # Artifact
    # =========================================================

    ARTIFACT_ERROR = "artifact_error"
    ARTIFACT_VALIDATION_ERROR = "artifact_validation_error"
    ARTIFACT_TIMESTAMP_MISSING = "artifact_timestamp_missing"
    ARTIFACT_INVALID_STATUS = "artifact_invalid_status"
    ARTIFACT_CONSISTENCY_ERROR = "artifact_consistency_error"

    # =========================================================
    # Kernel Runtime
    # =========================================================

    KERNEL_RUNTIME_ERROR = "kernel_runtime_error"
    SYSCALL_REGISTRY_ERROR = "syscall_registry_error"
    DUPLICATE_SYSCALL_REGISTRATION = "duplicate_syscall_registration"

    # =========================================================
    # Scheduler Runtime
    # =========================================================

    SCHEDULER_RUNTIME_ERROR = "scheduler_runtime_error"
    SCHEDULER_CONFIGURATION_ERROR = "scheduler_configuration_error"
    SCHEDULER_INVARIANT_VIOLATION = "scheduler_invariant_violation"
    INVALID_PROCESS_SCHEDULING = "invalid_process_scheduling"
    UNKNOWN_PROCESS = "unknown_process"

    # =========================================================
    # Pipeline Runtime
    # =========================================================

    PIPELINE_RUNTIME_ERROR = "pipeline_runtime_error"

    PIPELINE_EXECUTION_CONTRACT_VIOLATION = "pipeline_execution_contract_violation"

    PIPELINE_FINALIZE_CONTRACT_VIOLATION = "pipeline_finalize_contract_violation"

    PIPELINE_EXECUTION_RETURNED_NONE = "pipeline_execution_returned_none"

    # =========================================================
    # Runtime Execution
    # =========================================================

    RUNTIME_EXECUTION_ERROR = "runtime_execution_error"
    PROCESS_EXECUTION_ABORTED = "process_execution_aborted"

    RUNTIME_EXECUTION_CONTRACT_VIOLATION = "runtime_execution_contract_violation"

    # =========================================================
    # Tool Runtime
    # =========================================================

    TOOL_EXECUTION_ERROR = "tool_execution_error"
    TOOL_AUTHORIZATION_ERROR = "tool_authorization_error"
    TOOL_UNKNOWN = "tool_unknown"

    # =========================================================
    # LLM Runtime
    # =========================================================

    LLM_RUNTIME_ERROR = "llm_runtime_error"

    LLM_EXECUTION_CONTRACT_VIOLATION = "llm_execution_contract_violation"

    LLM_EMPTY_RESPONSE = "llm_empty_response"
    LLM_RETRY_EXHAUSTED = "llm_retry_exhausted"
    LLM_FALLBACK_EXHAUSTED = "llm_fallback_exhausted"
