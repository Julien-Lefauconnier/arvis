# tests/errors/test_error_normalization.py

from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from arvis.errors.base import ArvisError, ArvisExternalError, ArvisRuntimeError
from arvis.errors.normalization import normalize_error


class Model(BaseModel):
    x: int


def test_normalize_arvis_error_passthrough():
    error = ArvisRuntimeError("boom")

    assert normalize_error(error) is error


def test_normalize_unknown_exception_as_runtime_error():
    error = normalize_error(ValueError("invalid"))

    assert isinstance(error, ArvisRuntimeError)
    assert error.details["exception_type"] == "ValueError"


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

    assert isinstance(error, ArvisRuntimeError)
    assert error.details["json_error"] is True


def test_pydantic_validation_error_maps_to_runtime():
    try:
        Model(x="bad")
    except ValidationError as exc:
        error = normalize_error(exc)

    assert isinstance(error, ArvisRuntimeError)
    assert error.details["validation_error"] is True
