# arvis/errors/normalization.py

from __future__ import annotations

import asyncio
import json
from traceback import format_exception

from pydantic import ValidationError

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

    tb = "".join(format_exception(exc))

    if isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
        ),
    ):
        return ArvisExternalError(
            str(exc),
            details={
                "exception_type": type(exc).__name__,
            },
            traceback=tb,
        )

    if isinstance(exc, ValidationError):
        return ArvisRuntimeError(
            str(exc),
            details={
                "exception_type": type(exc).__name__,
                "validation_error": True,
            },
            traceback=tb,
        )

    if isinstance(exc, json.JSONDecodeError):
        return ArvisRuntimeError(
            str(exc),
            details={
                "exception_type": type(exc).__name__,
                "json_error": True,
            },
            traceback=tb,
        )

    return ArvisRuntimeError(
        str(exc),
        details={"exception_type": type(exc).__name__},
        traceback=tb,
    )
