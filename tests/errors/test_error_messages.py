# tests/errors/test_error_messages.py

from __future__ import annotations

from arvis.errors.messages import MAX_ERROR_MESSAGE_LENGTH, safe_exception_message


def test_safe_exception_message_removes_control_characters() -> None:
    exc = ValueError("bad\nvalue\twith\rcontrols")

    assert safe_exception_message(exc) == "bad value with controls"


def test_safe_exception_message_uses_fallback_for_empty_message() -> None:
    exc = RuntimeError("")

    assert (
        safe_exception_message(exc, fallback="fallback failure") == "fallback failure"
    )


def test_safe_exception_message_truncates_long_messages() -> None:
    exc = RuntimeError("x" * 1000)

    message = safe_exception_message(exc)

    assert len(message) == MAX_ERROR_MESSAGE_LENGTH
    assert message.endswith("...")
