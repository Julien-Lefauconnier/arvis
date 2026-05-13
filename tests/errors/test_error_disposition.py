# tests/errors/test_error_disposition.py

from __future__ import annotations

from arvis.errors.disposition import ErrorDisposition


def test_disposition_values():
    assert ErrorDisposition.CONTINUE == "continue"
    assert ErrorDisposition.RETRY == "retry"
    assert ErrorDisposition.FAIL_CLOSED == "fail_closed"
