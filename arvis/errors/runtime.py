# arvis/errors/runtime.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorCategory,
    ArvisErrorSeverity,
    ArvisRuntimeError,
    ErrorDomain,
    ErrorPolicy,
    ErrorSemantics,
)
from arvis.errors.codes import ErrorCode


class RuntimeDegradationError(ArvisRuntimeError):
    domain = ErrorDomain.CORE
    default_code = ErrorCode.RUNTIME_DEGRADATION

    severity = ArvisErrorSeverity.WARNING
    category = ArvisErrorCategory.DEGRADED
    policy = ErrorPolicy.DEGRADE

    degraded = True
    retryable = True

    def _semantics(self) -> tuple[ErrorSemantics, ...]:
        return (
            *super()._semantics(),
            ErrorSemantics.COMPUTATION_FAILURE,
        )


class CompositeComputationError(RuntimeDegradationError):
    default_code = ErrorCode.COMPOSITE_COMPUTATION_ERROR


class AdaptiveComputationError(RuntimeDegradationError):
    default_code = ErrorCode.ADAPTIVE_COMPUTATION_ERROR


class StabilityEvaluationError(RuntimeDegradationError):
    default_code = ErrorCode.STABILITY_EVALUATION_ERROR


class ProjectionComputationError(RuntimeDegradationError):
    default_code = ErrorCode.PROJECTION_COMPUTATION_ERROR
