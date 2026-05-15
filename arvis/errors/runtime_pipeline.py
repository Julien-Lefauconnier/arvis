# arvis/errors/runtime_pipeline.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ErrorDomain,
    ErrorPolicy,
)
from arvis.errors.codes import ErrorCode
from arvis.errors.pipeline import PipelineStageError


class PipelineRuntimeError(PipelineStageError):
    domain = ErrorDomain.PIPELINE
    default_code = ErrorCode.PIPELINE_RUNTIME_ERROR
    severity = ArvisErrorSeverity.ERROR
    policy = ErrorPolicy.FAIL_CLOSED
    replay_safe = False


class PipelineExecutionContractViolation(PipelineRuntimeError):
    default_code = ErrorCode.PIPELINE_EXECUTION_CONTRACT_VIOLATION
    severity = ArvisErrorSeverity.FATAL


class PipelineFinalizeContractViolation(
    PipelineExecutionContractViolation,
):
    default_code = ErrorCode.PIPELINE_FINALIZE_CONTRACT_VIOLATION


class PipelineExecutionReturnedNone(PipelineRuntimeError):
    default_code = ErrorCode.PIPELINE_EXECUTION_RETURNED_NONE
