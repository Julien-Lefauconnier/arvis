# tests/errors/test_observability_boundary.py

from __future__ import annotations

from arvis.errors.boundaries.observability import capture_observability_failure
from arvis.errors.context import DefaultErrorContext
from arvis.errors.manager import ErrorManager
from arvis.errors.observability import (
    ProjectionRefreshFailure,
    StabilityProjectionFailure,
)


def test_capture_observability_failure_attaches_typed_error() -> None:
    ctx = DefaultErrorContext()
    exc = RuntimeError("projection exploded")

    payload = capture_observability_failure(
        ctx,
        exc,
        error_cls=ProjectionRefreshFailure,
        message="Projection refresh failed",
        component="ProjectionStage.refresh",
    )

    assert payload["type"] == "ProjectionRefreshFailure"
    assert payload["code"] == "projection_refresh_failure"
    assert payload["domain"] == "core"
    assert payload["degraded"] is True
    assert payload["retryable"] is True
    assert payload["replay_safe"] is True
    assert payload["details"]["component"] == "ProjectionStage.refresh"
    assert payload["details"]["runtime_degraded"] is True
    assert payload["origin"]["component"] == "ProjectionStage.refresh"
    assert payload["origin"]["subsystem"] == "observability"
    assert payload["cause"]["error_type"] == "RuntimeError"


def test_capture_observability_failure_updates_runtime_degradation() -> None:
    ctx = DefaultErrorContext()

    capture_observability_failure(
        ctx,
        ValueError("bad stability projection"),
        error_cls=StabilityProjectionFailure,
        message="Stability projection failed",
        component="PipelineObservabilityService",
    )

    degradation = ErrorManager.runtime_degradation_state(ctx)
    stats = ErrorManager.statistics(ctx)

    assert degradation["active"] is True
    assert degradation["count"] == 1
    assert degradation["last_code"] == "stability_projection_failure"
    assert degradation["domains"]["core"] == 1
    assert stats["degraded"] == 1
    assert stats["warning"] == 1


def test_capture_observability_failure_merges_details() -> None:
    ctx = DefaultErrorContext()

    payload = capture_observability_failure(
        ctx,
        RuntimeError("boom"),
        error_cls=ProjectionRefreshFailure,
        message="Projection refresh failed",
        component="ProjectionStage.refresh",
        details={"stage": "projection", "attempt": 1},
    )

    assert payload["details"]["component"] == "ProjectionStage.refresh"
    assert payload["details"]["stage"] == "projection"
    assert payload["details"]["attempt"] == 1
