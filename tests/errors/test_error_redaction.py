# tests/errors/test_error_redaction.py

from __future__ import annotations

from arvis.errors.redaction import (
    REDACTED,
    redact_error_payload,
)


def test_redact_traceback_by_default():
    payload = {
        "traceback": "SECRET_TRACEBACK",
    }

    redacted = redact_error_payload(payload)

    assert "traceback" not in redacted


def test_include_traceback_when_requested():
    payload = {
        "traceback": "TRACE",
    }

    redacted = redact_error_payload(
        payload,
        include_traceback=True,
    )

    assert redacted["traceback"] == REDACTED


def test_remove_error_id_when_disabled():
    payload = {
        "error_id": "abc123",
    }

    redacted = redact_error_payload(
        payload,
        include_error_id=False,
    )

    assert "error_id" not in redacted


def test_redact_sensitive_exact_key():
    payload = {
        "token": "SECRET",
    }

    redacted = redact_error_payload(payload)

    assert redacted["token"] == REDACTED


def test_redact_sensitive_fragment_key():
    payload = {
        "user_access_token": "SECRET",
    }

    redacted = redact_error_payload(payload)

    assert redacted["user_access_token"] == REDACTED


def test_redact_nested_sensitive_values():
    payload = {
        "details": {
            "api_key": "SECRET",
        }
    }

    redacted = redact_error_payload(payload)

    assert redacted["details"]["api_key"] == REDACTED


def test_redact_sensitive_values_inside_list():
    payload = {
        "errors": [
            {
                "authorization": "SECRET",
            }
        ]
    }

    redacted = redact_error_payload(payload)

    nested = redacted["errors"][0]

    assert nested["authorization"] == REDACTED


def test_preserve_non_sensitive_values():
    payload = {
        "code": "RUNTIME_ERROR",
        "retryable": True,
    }

    redacted = redact_error_payload(payload)

    assert redacted["code"] == "RUNTIME_ERROR"
    assert redacted["retryable"] is True


def test_preserve_fingerprint():
    payload = {
        "fingerprint": "stable-fingerprint",
    }

    redacted = redact_error_payload(payload)

    assert redacted["fingerprint"] == "stable-fingerprint"
