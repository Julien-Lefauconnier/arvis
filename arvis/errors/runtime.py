# arvis/errors/runtime.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorSeverity,
    ArvisRuntimeError,
    ErrorDomain,
    ErrorPolicy,
    ErrorSemantics,
)


class RuntimeDegradationError(ArvisRuntimeError):
    domain = ErrorDomain.CORE
    default_code = "RUNTIME_DEGRADATION"

    severity = ArvisErrorSeverity.WARNING
    policy = ErrorPolicy.DEGRADE

    degraded = True
    retryable = True

    def _semantics(self) -> tuple[ErrorSemantics, ...]:
        return (
            *super()._semantics(),
            ErrorSemantics.COMPUTATION_FAILURE,
        )


class CompositeComputationError(RuntimeDegradationError):
    default_code = "COMPOSITE_COMPUTATION_ERROR"


class AdaptiveComputationError(RuntimeDegradationError):
    default_code = "ADAPTIVE_COMPUTATION_ERROR"


class StabilityEvaluationError(RuntimeDegradationError):
    default_code = "STABILITY_EVALUATION_ERROR"


class ProjectionComputationError(RuntimeDegradationError):
    default_code = "PROJECTION_COMPUTATION_ERROR"
