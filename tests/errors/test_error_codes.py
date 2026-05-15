# tests/errors/test_error_codes.py

from __future__ import annotations

from arvis.errors.codes import ErrorCode


def test_error_codes_are_unique():
    values = [e.value for e in ErrorCode]

    assert len(values) == len(set(values))


def test_error_code_string_values():
    assert ErrorCode.RUNTIME_ERROR == "runtime_error"
    assert ErrorCode.PIPELINE_STAGE_FAILURE == ("pipeline_stage_failure")
