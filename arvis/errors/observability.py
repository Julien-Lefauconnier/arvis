# arvis/errors/observability.py

from __future__ import annotations

from arvis.errors.base import (
    ErrorDomain,
)
from arvis.errors.codes import ErrorCode
from arvis.errors.runtime import RuntimeDegradationError


class ObservabilityRuntimeError(RuntimeDegradationError):
    domain = ErrorDomain.CORE
    default_code = ErrorCode.OBSERVABILITY_RUNTIME_ERROR


class ProjectionRefreshFailure(ObservabilityRuntimeError):
    default_code = ErrorCode.PROJECTION_REFRESH_FAILURE


class StabilityProjectionFailure(ObservabilityRuntimeError):
    default_code = ErrorCode.STABILITY_PROJECTION_FAILURE


class FastDynamicsSnapshotFailure(ObservabilityRuntimeError):
    default_code = ErrorCode.FAST_DYNAMICS_SNAPSHOT_FAILURE


class QuadraticLyapunovSnapshotFailure(
    ObservabilityRuntimeError,
):
    default_code = ErrorCode.QUADRATIC_LYAPUNOV_SNAPSHOT_FAILURE
