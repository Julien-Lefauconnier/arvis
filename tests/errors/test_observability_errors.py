# tests/errors/test_observability_errors.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ErrorPolicy,
)
from arvis.errors.codes import ErrorCode
from arvis.errors.observability import (
    FastDynamicsSnapshotFailure,
    ObservabilityRuntimeError,
    ProjectionRefreshFailure,
    QuadraticLyapunovSnapshotFailure,
    StabilityProjectionFailure,
)


def test_observability_runtime_error_metadata() -> None:
    error = ObservabilityRuntimeError(
        "observability degraded",
    )

    metadata = error.metadata

    assert metadata.code == ErrorCode.OBSERVABILITY_RUNTIME_ERROR
    assert metadata.severity == ArvisErrorSeverity.WARNING
    assert metadata.policy == ErrorPolicy.DEGRADE

    assert metadata.degraded is True
    assert metadata.retryable is True
    assert metadata.replay_safe is True


def test_projection_refresh_failure_serialization() -> None:
    error = ProjectionRefreshFailure(
        "projection refresh failed",
    )

    payload = error.to_dict()

    assert payload["code"] == ErrorCode.PROJECTION_REFRESH_FAILURE
    assert payload["type"] == "ProjectionRefreshFailure"


def test_stability_projection_failure_serialization() -> None:
    error = StabilityProjectionFailure(
        "stability projection failed",
    )

    payload = error.to_dict()

    assert payload["code"] == ErrorCode.STABILITY_PROJECTION_FAILURE


def test_fast_dynamics_snapshot_failure_serialization() -> None:
    error = FastDynamicsSnapshotFailure(
        "fast dynamics failed",
    )

    payload = error.to_dict()

    assert payload["code"] == ErrorCode.FAST_DYNAMICS_SNAPSHOT_FAILURE


def test_quadratic_lyapunov_snapshot_failure_serialization() -> None:
    error = QuadraticLyapunovSnapshotFailure(
        "quadratic snapshot failed",
    )

    payload = error.to_dict()

    assert payload["code"] == ErrorCode.QUADRATIC_LYAPUNOV_SNAPSHOT_FAILURE
