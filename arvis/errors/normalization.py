# arvis/errors/normalization.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisError,
    ArvisExternalError,
    ArvisRuntimeError,
)


def normalize_error(exc: BaseException) -> ArvisError:
    """
    Convert any exception into an ArvisError.

    This is the canonical boundary adapter for:
    - broad except blocks
    - syscall wrappers
    - pipeline stage guards
    - external adapter failures
    """

    if isinstance(exc, ArvisError):
        return exc

    if isinstance(exc, TimeoutError | ConnectionError):
        return ArvisExternalError(
            str(exc),
            details={"exception_type": type(exc).__name__},
        )

    return ArvisRuntimeError(
        str(exc),
        details={"exception_type": type(exc).__name__},
    )
