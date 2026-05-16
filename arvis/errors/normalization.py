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
from arvis.errors.classification import (
    BoundaryHint,
    ErrorClassificationKind,
    classify_exception,
)
from arvis.errors.codes import ErrorCode
from arvis.errors.provenance import cause_from_exception
from arvis.errors.runtime import RuntimeDegradationError


def normalize_error(
    exc: BaseException,
    *,
    boundary: BoundaryHint | None = None,
) -> ArvisError:
    """
    Convert any exception into an ArvisError.

    Classification is semantic.
    Normalization is mechanical.
    """

    if isinstance(exc, ArvisError):
        return exc

    tb = "".join(format_exception(exc))
    cause = cause_from_exception(exc)
    classification = classify_exception(exc, boundary=boundary)

    details: dict[str, str | int | float | bool | None] = {
        "exception_type": type(exc).__name__,
        "classification": classification.kind.value,
    }

    if (
        isinstance(
            exc,
            (
                TimeoutError,
                ConnectionError,
                asyncio.TimeoutError,
            ),
        )
        or classification.kind == ErrorClassificationKind.EXTERNAL
    ):
        return ArvisExternalError(
            str(exc),
            code=ErrorCode.EXTERNAL_ERROR,
            details=details,
            cause=cause,
            traceback=tb,
        )

    if isinstance(exc, json.JSONDecodeError) or (
        classification.kind == ErrorClassificationKind.INVALID_PAYLOAD
    ):
        return InvalidIRPayloadError(
            str(exc),
            details={
                **details,
                "json_error": isinstance(exc, json.JSONDecodeError),
            },
            code=ErrorCode.INVALID_IR_PAYLOAD,
            cause=cause,
            traceback=tb,
        )

    if classification.kind == ErrorClassificationKind.CONTRACT:
        return ArvisRuntimeError(
            str(exc),
            code=ErrorCode.RUNTIME_ERROR,
            domain=classification.domain,
            policy=classification.policy,
            retryable=classification.retryable,
            deterministic=classification.deterministic,
            replay_safe=classification.replay_safe,
            degraded=classification.degraded,
            details={
                **details,
                "validation_error": isinstance(exc, ValidationError),
                "contract_failure": True,
            },
            cause=cause,
            traceback=tb,
        )

    if classification.kind == ErrorClassificationKind.INVARIANT:
        return ArvisInvariantViolation(
            str(exc) or "Invariant violated",
            code=ErrorCode.INVARIANT_VIOLATION,
            domain=classification.domain,
            policy=classification.policy,
            retryable=classification.retryable,
            deterministic=classification.deterministic,
            replay_safe=classification.replay_safe,
            degraded=classification.degraded,
            details={
                **details,
                "assertion_error": isinstance(exc, AssertionError),
                "value_error": isinstance(exc, ValueError),
            },
            cause=cause,
            traceback=tb,
        )

    if classification.kind == ErrorClassificationKind.COMPUTATION:
        return RuntimeDegradationError(
            str(exc),
            code=ErrorCode.RUNTIME_DEGRADATION,
            domain=classification.domain,
            policy=classification.policy,
            retryable=classification.retryable,
            deterministic=classification.deterministic,
            replay_safe=classification.replay_safe,
            degraded=classification.degraded,
            details={
                **details,
                "computation_failure": True,
            },
            cause=cause,
            traceback=tb,
        )

    return ArvisRuntimeError(
        str(exc),
        code=ErrorCode.RUNTIME_ERROR,
        domain=classification.domain,
        policy=classification.policy,
        retryable=classification.retryable,
        deterministic=classification.deterministic,
        replay_safe=classification.replay_safe,
        degraded=classification.degraded,
        details={
            **details,
            "type_error": isinstance(exc, TypeError),
        },
        cause=cause,
        traceback=tb,
    )
