# arvis/errors/normalization.py

from __future__ import annotations

import asyncio
import json
from traceback import format_exception

from pydantic import ValidationError

from arvis.errors.api import InvalidIRPayloadError
from arvis.errors.base import (
    ArvisError,
    ArvisExternalError,
    ArvisInvariantViolation,
    ArvisRuntimeError,
)
from arvis.errors.codes import ErrorCode
from arvis.errors.provenance import cause_from_exception


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
    cause = cause_from_exception(exc)

    details: dict[str, str | int | float | bool | None] = {
        "exception_type": type(exc).__name__,
    }

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
            code=ErrorCode.EXTERNAL_ERROR,
            details=details,
            cause=cause,
            traceback=tb,
        )

    if isinstance(exc, ValidationError):
        return ArvisRuntimeError(
            str(exc),
            details={
                **details,
                "validation_error": True,
            },
            code=ErrorCode.RUNTIME_ERROR,
            cause=cause,
            traceback=tb,
        )

    if isinstance(exc, json.JSONDecodeError):
        return InvalidIRPayloadError(
            str(exc),
            details={
                **details,
                "json_error": True,
            },
            code=ErrorCode.INVALID_IR_PAYLOAD,
            cause=cause,
            traceback=tb,
        )

    if isinstance(exc, AssertionError):
        return ArvisInvariantViolation(
            str(exc) or "Assertion invariant violated",
            code=ErrorCode.INVARIANT_VIOLATION,
            details={
                **details,
                "assertion_error": True,
            },
            cause=cause,
            traceback=tb,
        )

    if isinstance(exc, ValueError):
        return ArvisInvariantViolation(
            str(exc),
            code=ErrorCode.INVARIANT_VIOLATION,
            details={
                **details,
                "value_error": True,
            },
            cause=cause,
            traceback=tb,
        )

    if isinstance(exc, TypeError):
        return ArvisRuntimeError(
            str(exc),
            code=ErrorCode.RUNTIME_ERROR,
            details={
                **details,
                "type_error": True,
            },
            cause=cause,
            traceback=tb,
        )

    return ArvisRuntimeError(
        str(exc),
        code=ErrorCode.RUNTIME_ERROR,
        details=details,
        cause=cause,
        traceback=tb,
    )
