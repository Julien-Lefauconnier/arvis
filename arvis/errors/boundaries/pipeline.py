# arvis/errors/boundaries/pipeline.py

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.errors.pipeline import PipelineStageDegradedError
from arvis.errors.provenance import ErrorOrigin, cause_from_exception
from arvis.errors.types import ErrorDetails, ErrorPayload


def capture_pipeline_degraded_failure(
    ctx: Any,
    exc: Exception,
    *,
    component: str,
    message: str,
    details: ErrorDetails | None = None,
) -> ErrorPayload:
    """
    Canonical fail-soft pipeline boundary adapter.

    This helper maps recoverable pipeline failures into a structured
    degraded ARVIS error while preserving origin and exception cause.
    """
    merged_details: ErrorDetails = {
        "component": component,
        "runtime_degraded": True,
    }

    if details:
        merged_details.update(details)

    wrapped = PipelineStageDegradedError(
        message=message,
        details=merged_details,
        origin=ErrorOrigin(
            component=component,
            subsystem="pipeline",
        ),
        cause=cause_from_exception(exc),
    )

    return ErrorManager.attach(ctx, wrapped)
