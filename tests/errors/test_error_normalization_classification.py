# tests/errors/test_error_normalization_classification.py

from __future__ import annotations

import json

from arvis.errors import normalize_error
from arvis.errors.api import InvalidIRPayloadError
from arvis.errors.base import (
    ArvisExternalError,
    ArvisInvariantViolation,
    ArvisRuntimeError,
)
from arvis.errors.runtime import RuntimeDegradationError


def test_normalize_timeout_preserves_external_semantics() -> None:
    error = normalize_error(TimeoutError("timeout"))

    assert isinstance(error, ArvisExternalError)
    assert error.retryable is True
    assert error.deterministic is False
    assert error.replay_safe is False
    assert error.details["classification"] == "external"


def test_normalize_json_error_as_invalid_payload() -> None:
    exc = json.JSONDecodeError("bad json", "{", 0)

    error = normalize_error(exc)

    assert isinstance(error, InvalidIRPayloadError)
    assert error.details["classification"] == "invalid_payload"


def test_normalize_value_error_remains_invariant_by_default() -> None:
    error = normalize_error(ValueError("bad value"))

    assert isinstance(error, ArvisInvariantViolation)
    assert error.replay_safe is False
    assert error.details["classification"] == "invariant"


def test_normalize_with_computation_boundary_becomes_degraded_runtime() -> None:
    error = normalize_error(
        ValueError("bad numeric value"),
        boundary="computation",
    )

    assert isinstance(error, RuntimeDegradationError)
    assert error.degraded is True
    assert error.retryable is True
    assert error.replay_safe is True
    assert error.details["classification"] == "computation"


def test_normalize_with_contract_boundary_becomes_runtime_contract_error() -> None:
    error = normalize_error(
        TypeError("invalid adapter shape"),
        boundary="contract",
    )

    assert isinstance(error, ArvisRuntimeError)
    assert error.policy == "fail_closed"
    assert error.replay_safe is False
    assert error.details["classification"] == "contract"
    assert error.details["contract_failure"] is True
