# tests/errors/test_error_semantics.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisExternalError,
    ArvisRuntimeError,
    ErrorPolicy,
    ErrorSemantics,
)


def test_runtime_error_semantics():
    error = ArvisRuntimeError("runtime")

    semantics = {s.value for s in error.metadata.semantics}

    assert ErrorSemantics.DETERMINISTIC.value in semantics
    assert ErrorSemantics.REPLAY_SAFE.value in semantics
    assert error.metadata.policy == ErrorPolicy.HALT_PROCESS


def test_external_error_semantics():
    error = ArvisExternalError("external")

    semantics = {s.value for s in error.metadata.semantics}

    assert ErrorSemantics.NON_DETERMINISTIC.value in semantics
    assert ErrorSemantics.TRANSIENT.value in semantics
    assert error.metadata.policy == ErrorPolicy.RETRY


def test_runtime_error_observable():
    error = ArvisRuntimeError("runtime")

    semantics = {s.value for s in error.metadata.semantics}

    assert "observable" in semantics
