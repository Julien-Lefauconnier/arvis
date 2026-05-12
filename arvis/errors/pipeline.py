# arvis/errors/pipeline.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisRuntimeError,
)


class PipelineStageError(ArvisRuntimeError):
    default_code = "PIPELINE_STAGE_ERROR"
    severity = ArvisErrorSeverity.ERROR


class PipelineStageDegradedError(PipelineStageError):
    default_code = "PIPELINE_STAGE_DEGRADED"
    severity = ArvisErrorSeverity.WARNING
    degraded = True


class PipelineFailClosedError(PipelineStageError):
    default_code = "PIPELINE_FAIL_CLOSED"
    replay_safe = True
