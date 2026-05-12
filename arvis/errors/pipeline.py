# arvis/errors/pipeline.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisRuntimeError,
    ErrorDomain,
    ErrorPolicy,
)


class PipelineStageError(ArvisRuntimeError):
    domain = ErrorDomain.PIPELINE
    default_code = "PIPELINE_STAGE_ERROR"
    severity = ArvisErrorSeverity.ERROR


class PipelineStageDegradedError(PipelineStageError):
    default_code = "PIPELINE_STAGE_DEGRADED"
    severity = ArvisErrorSeverity.WARNING
    policy = ErrorPolicy.DEGRADE
    degraded = True


class PipelineFailClosedError(PipelineStageError):
    default_code = "PIPELINE_FAIL_CLOSED"
    replay_safe = True
    policy = ErrorPolicy.FAIL_CLOSED
    degraded = False
    retryable = False
