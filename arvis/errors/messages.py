# arvis/errors/messages.py

from __future__ import annotations

MAX_ERROR_MESSAGE_LENGTH = 512


def safe_exception_message(
    exc: BaseException, *, fallback: str = "runtime failure"
) -> str:
    raw = str(exc).strip()

    if not raw:
        raw = fallback

    sanitized = "".join(
        char if char.isprintable() and char not in {"\n", "\r", "\t"} else " "
        for char in raw
    )

    sanitized = " ".join(sanitized.split())

    if len(sanitized) > MAX_ERROR_MESSAGE_LENGTH:
        return sanitized[: MAX_ERROR_MESSAGE_LENGTH - 3] + "..."

    return sanitized
