# tests/errors/test_error_traceback.py

from __future__ import annotations

from arvis.errors.normalization import normalize_error


def test_normalized_error_contains_traceback():
    try:
        raise ValueError("boom")
    except ValueError as exc:
        error = normalize_error(exc)

    assert error.traceback is not None
    assert "ValueError" in error.traceback


def test_error_contains_error_id():
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        error = normalize_error(exc)

    payload = error.to_dict()

    assert payload["error_id"]
    assert isinstance(payload["error_id"], str)


def test_error_id_is_unique():
    e1 = normalize_error(RuntimeError("x"))
    e2 = normalize_error(RuntimeError("x"))

    assert e1.error_id != e2.error_id
