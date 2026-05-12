# tests/errors/test_pipeline_errors.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorCategory,
    ArvisErrorSeverity,
)
from arvis.errors.pipeline import (
    PipelineFailClosedError,
    PipelineStageDegradedError,
    PipelineStageError,
)


def test_pipeline_stage_error():
    error = PipelineStageError("stage error")

    assert error.category == ArvisErrorCategory.RUNTIME
    assert error.severity == ArvisErrorSeverity.ERROR


def test_pipeline_stage_degraded_error():
    error = PipelineStageDegradedError("degraded")

    assert error.severity == ArvisErrorSeverity.WARNING
    assert error.degraded is True


def test_pipeline_fail_closed_error():
    error = PipelineFailClosedError("fail closed")

    assert error.replay_safe is True
