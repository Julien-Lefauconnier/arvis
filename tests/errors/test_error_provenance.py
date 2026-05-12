# tests/errors/test_error_provenance.py

from __future__ import annotations

from arvis.errors.base import ArvisRuntimeError
from arvis.errors.manager import ErrorManager
from arvis.errors.provenance import ErrorCause, ErrorOrigin, build_error_fingerprint


def test_error_origin_serializes_sparse_fields():
    origin = ErrorOrigin(component="gate", stage="projection")

    assert origin.to_dict() == {
        "component": "gate",
        "stage": "projection",
    }


def test_error_cause_serializes_optional_fingerprint():
    cause = ErrorCause(
        code="ROOT",
        error_type="RootError",
        fingerprint="err-root",
    )

    assert cause.to_dict() == {
        "code": "ROOT",
        "error_type": "RootError",
        "fingerprint": "err-root",
    }


def test_error_payload_contains_provenance_and_fingerprint():
    error = ArvisRuntimeError(
        "boom",
        code="BOOM",
        origin=ErrorOrigin(component="control", subsystem="runtime"),
        cause=ErrorCause(code="ROOT", error_type="RootError"),
    )

    payload = error.to_dict()

    assert payload["fingerprint"]
    assert payload["created_at"]
    assert isinstance(payload["monotonic_ns"], int)
    assert payload["origin"]["component"] == "control"
    assert payload["cause"]["code"] == "ROOT"
    assert payload["sensitive"] is False
    assert payload["redactable"] is True


def test_error_fingerprint_is_stable_for_same_semantics():
    fp1 = build_error_fingerprint(
        code="X",
        domain="core",
        category="runtime",
        severity="error",
        policy="halt_process",
        semantics=("replay_safe", "deterministic"),
        deterministic=True,
        replay_safe=True,
        degraded=False,
    )
    fp2 = build_error_fingerprint(
        code="X",
        domain="core",
        category="runtime",
        severity="error",
        policy="halt_process",
        semantics=("deterministic", "replay_safe"),
        deterministic=True,
        replay_safe=True,
        degraded=False,
    )

    assert fp1 == fp2


def test_capture_exception_accepts_origin(ctx):
    payload = ErrorManager.capture_exception(
        ctx,
        RuntimeError("boom"),
        code="CONTROL_FAILURE",
        origin=ErrorOrigin(component="control", stage="compute"),
    )

    assert payload["code"] == "CONTROL_FAILURE"
    assert payload["origin"]["component"] == "control"
    assert payload["origin"]["stage"] == "compute"
    assert payload["cause"]["error_type"] == "RuntimeError"
