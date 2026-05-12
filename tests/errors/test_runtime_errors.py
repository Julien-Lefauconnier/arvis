# tests/errors/test_runtime_errors.py

from arvis.errors.base import (
    ErrorPolicy,
)
from arvis.errors.runtime import (
    CompositeComputationError,
    RuntimeDegradationError,
)


def test_runtime_degradation_defaults():
    error = RuntimeDegradationError("runtime degraded")

    assert error.degraded is True
    assert error.retryable is True
    assert error.policy == ErrorPolicy.DEGRADE


def test_runtime_degradation_semantics():
    error = CompositeComputationError("composite")

    semantics = {s.value for s in error.metadata.semantics}

    assert "degraded_runtime" in semantics
    assert "recoverable" in semantics
    assert "observable" in semantics
    assert "computation_failure" in semantics
