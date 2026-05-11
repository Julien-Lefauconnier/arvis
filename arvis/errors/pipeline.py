# arvis/errors/pipeline.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisRuntimeError,
)


class PipelineStageError(ArvisRuntimeError):
    severity = ArvisErrorSeverity.ERROR


class PipelineStageDegradedError(PipelineStageError):
    severity = ArvisErrorSeverity.WARNING
    degraded = True


class PipelineFailClosedError(PipelineStageError):
    replay_safe = True
