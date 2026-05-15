# tests/errors/test_error_normalization.py

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from arvis.errors.api import InvalidIRPayloadError
from arvis.errors.base import (
    ArvisError,
    ArvisExternalError,
    ArvisInvariantViolation,
    ArvisRuntimeError,
)
from arvis.errors.normalization import normalize_error


class Model(BaseModel):
    x: int


def test_normalize_arvis_error_passthrough():
    error = ArvisRuntimeError("boom")

    assert normalize_error(error) is error


def test_normalize_value_error_as_invariant_violation():
    error = normalize_error(ValueError("invalid"))

    assert isinstance(error, ArvisInvariantViolation)
    assert error.details["exception_type"] == "ValueError"
    assert error.details["value_error"] is True


def test_normalize_timeout_as_external_error():
    error = normalize_error(TimeoutError("timeout"))

    assert isinstance(error, ArvisExternalError)
    assert error.retryable is True
    assert error.deterministic is False


def test_normalize_returns_arvis_error():
    error = normalize_error(Exception("boom"))

    assert isinstance(error, ArvisError)


def test_asyncio_timeout_maps_to_external():
    error = normalize_error(TimeoutError())

    assert isinstance(error, ArvisExternalError)


def test_json_decode_error_maps_to_runtime():
    try:
        json.loads("{")
    except json.JSONDecodeError as exc:
        error = normalize_error(exc)

    assert isinstance(error, InvalidIRPayloadError)
    assert error.details["json_error"] is True


def test_pydantic_validation_error_maps_to_runtime():
    try:
        Model(x="bad")
    except ValidationError as exc:
        error = normalize_error(exc)

    assert isinstance(error, ArvisRuntimeError)
    assert error.details["validation_error"] is True


def test_assertion_error_maps_to_invariant_violation():
    error = normalize_error(AssertionError("broken invariant"))

    assert isinstance(error, ArvisInvariantViolation)
    assert error.details["assertion_error"] is True


def test_type_error_maps_to_runtime_error():
    error = normalize_error(TypeError("bad type"))

    assert isinstance(error, ArvisRuntimeError)
    assert error.details["type_error"] is True


def test_normalize_generic_exception_preserves_cause():
    error = normalize_error(Exception("boom"))

    assert error.cause is not None
    assert error.cause.error_type == "Exception"
