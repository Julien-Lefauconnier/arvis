# arvis/errors/boundaries/observability.py

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.errors.observability import ObservabilityRuntimeError
from arvis.errors.provenance import ErrorOrigin, cause_from_exception
from arvis.errors.types import ErrorDetails, ErrorPayload


def capture_observability_failure(
    ctx: Any,
    exc: Exception,
    *,
    error_cls: type[ObservabilityRuntimeError],
    message: str,
    component: str,
    details: ErrorDetails | None = None,
) -> ErrorPayload:
    """
    Canonical observability boundary adapter.

    This helper preserves the original exception cause while mapping
    runtime failures into the observability degradation taxonomy.
    """
    merged_details: ErrorDetails = {
        "component": component,
        "runtime_degraded": True,
    }

    if details:
        merged_details.update(details)

    wrapped = error_cls(
        message,
        details=merged_details,
        origin=ErrorOrigin(
            component=component,
            subsystem="observability",
        ),
        cause=cause_from_exception(exc),
    )

    diagnostics = getattr(
        getattr(ctx, "observability", None),
        "diagnostics",
        None,
    )

    if diagnostics is not None:
        if component not in diagnostics.degraded_components:
            diagnostics.degraded_components.append(component)

        if message not in diagnostics.warnings:
            diagnostics.warnings.append(message)

    return ErrorManager.attach(ctx, wrapped)
