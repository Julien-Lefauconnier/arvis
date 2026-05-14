# arvis/errors/codes.py

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    # =========================================================
    # Generic
    # =========================================================

    ARVIS_ERROR = "ARVIS_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    DOMAIN_ERROR = "DOMAIN_ERROR"
    EXTERNAL_ERROR = "EXTERNAL_ERROR"
    INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
    DEGRADED_MODE = "DEGRADED_MODE"

    # =========================================================
    # API
    # =========================================================

    API_ERROR = "API_ERROR"
    COGNITIVE_STATE_REQUIRED = "COGNITIVE_STATE_REQUIRED"
    INVALID_IR_PAYLOAD = "INVALID_IR_PAYLOAD"

    # =========================================================
    # Pipeline
    # =========================================================

    PIPELINE_STAGE_FAILURE = "PIPELINE_STAGE_FAILURE"
    PIPELINE_STAGE_ERROR = "PIPELINE_STAGE_ERROR"
    PIPELINE_STAGE_DEGRADED = "PIPELINE_STAGE_DEGRADED"
    PIPELINE_FAIL_CLOSED = "PIPELINE_FAIL_CLOSED"

    # =========================================================
    # Runtime
    # =========================================================

    RUNTIME_DEGRADATION = "RUNTIME_DEGRADATION"

    # =========================================================
    # Computation
    # =========================================================

    COMPUTATION_FAILURE = "COMPUTATION_FAILURE"
    PROJECTION_COMPUTATION_ERROR = "PROJECTION_COMPUTATION_ERROR"
    COMPOSITE_COMPUTATION_ERROR = "COMPOSITE_COMPUTATION_ERROR"
    ADAPTIVE_COMPUTATION_ERROR = "ADAPTIVE_COMPUTATION_ERROR"
    STABILITY_EVALUATION_ERROR = "STABILITY_EVALUATION_ERROR"

    # =========================================================
    # Kernel
    # =========================================================

    KERNEL_ERROR = "KERNEL_ERROR"
    KERNEL_FAIL_CLOSED = "KERNEL_FAIL_CLOSED"
    KERNEL_INVARIANT_VIOLATION = "KERNEL_INVARIANT_VIOLATION"
    KERNEL_DEGRADED_WARNING = "KERNEL_DEGRADED_WARNING"

    # =========================================================
    # Replay
    # =========================================================

    REPLAY_ERROR = "REPLAY_ERROR"
    SECURITY_ERROR = "SECURITY_ERROR"
    REPLAY_VERIFICATION_FAILED = "REPLAY_VERIFICATION_FAILED"
    REPLAY_GLOBAL_COMMITMENT_MISSING = "REPLAY_GLOBAL_COMMITMENT_MISSING"
    REPLAY_GLOBAL_COMMITMENT_MISMATCH = "REPLAY_GLOBAL_COMMITMENT_MISMATCH"
    REPLAY_COGNITIVE_STATE_MISSING = "REPLAY_COGNITIVE_STATE_MISSING"

    # =========================================================
    # Syscalls
    # =========================================================

    SYSCALL_EXECUTION_ERROR = "SYSCALL_EXECUTION_ERROR"
    UNKNOWN_SYSCALL = "UNKNOWN_SYSCALL"
    INVALID_SYSCALL_ARGS = "INVALID_SYSCALL_ARGS"
    INVALID_SYSCALL_RETURN_TYPE = "INVALID_SYSCALL_RETURN_TYPE"
    SYSCALL_VALIDATION_ERROR = "SYSCALL_VALIDATION_ERROR"
    SYSCALL_REPLAY_ERROR = "SYSCALL_REPLAY_ERROR"
    SYSCALL_EXTERNAL_DEPENDENCY_ERROR = "SYSCALL_EXTERNAL_DEPENDENCY_ERROR"
