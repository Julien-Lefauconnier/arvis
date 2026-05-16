# arvis/errors/classification.py

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from pydantic import ValidationError

from arvis.errors.base import ErrorDomain, ErrorPolicy


class ErrorClassificationKind(StrEnum):
    INVARIANT = "invariant"
    CONTRACT = "contract"
    RUNTIME = "runtime"
    COMPUTATION = "computation"
    EXTERNAL = "external"
    INVALID_PAYLOAD = "invalid_payload"


@dataclass(slots=True, frozen=True)
class ErrorClassification:
    kind: ErrorClassificationKind
    domain: ErrorDomain
    policy: ErrorPolicy
    retryable: bool
    deterministic: bool
    replay_safe: bool
    degraded: bool


BoundaryHint = Literal[
    "api",
    "pipeline",
    "llm",
    "syscall",
    "replay",
    "runtime",
    "external",
    "computation",
    "contract",
    "invariant",
    "invalid_payload",
]


def classify_exception(
    exc: BaseException,
    *,
    boundary: BoundaryHint | None = None,
) -> ErrorClassification:
    """
    Classify a Python exception into ARVIS runtime semantics.

    This layer is intentionally semantic:
    it decides how ARVIS should interpret a failure before normalization
    converts it into a concrete ArvisError subclass.
    """

    if boundary == "external":
        return _external()

    if boundary == "invalid_payload":
        return _invalid_payload()

    if boundary == "contract":
        return _contract()

    if boundary == "invariant":
        return _invariant()

    if boundary == "computation":
        return _computation()

    if isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
        ),
    ):
        return _external()

    if isinstance(exc, json.JSONDecodeError):
        return _invalid_payload()

    if isinstance(exc, ValidationError):
        return _contract()

    if isinstance(exc, AssertionError):
        return _invariant()

    if isinstance(exc, ValueError):
        # Backward-compatible default:
        # ValueError remains invariant unless a boundary gives stronger meaning.
        return _invariant()

    if isinstance(exc, TypeError):
        return _runtime()

    return _runtime()


def _invariant() -> ErrorClassification:
    return ErrorClassification(
        kind=ErrorClassificationKind.INVARIANT,
        domain=ErrorDomain.KERNEL,
        policy=ErrorPolicy.FAIL_CLOSED,
        retryable=False,
        deterministic=True,
        replay_safe=False,
        degraded=False,
    )


def _contract() -> ErrorClassification:
    return ErrorClassification(
        kind=ErrorClassificationKind.CONTRACT,
        domain=ErrorDomain.CORE,
        policy=ErrorPolicy.FAIL_CLOSED,
        retryable=False,
        deterministic=True,
        replay_safe=False,
        degraded=False,
    )


def _runtime() -> ErrorClassification:
    return ErrorClassification(
        kind=ErrorClassificationKind.RUNTIME,
        domain=ErrorDomain.CORE,
        policy=ErrorPolicy.HALT_PROCESS,
        retryable=False,
        deterministic=True,
        replay_safe=True,
        degraded=False,
    )


def _computation() -> ErrorClassification:
    return ErrorClassification(
        kind=ErrorClassificationKind.COMPUTATION,
        domain=ErrorDomain.CORE,
        policy=ErrorPolicy.DEGRADE,
        retryable=True,
        deterministic=True,
        replay_safe=True,
        degraded=True,
    )


def _external() -> ErrorClassification:
    return ErrorClassification(
        kind=ErrorClassificationKind.EXTERNAL,
        domain=ErrorDomain.EXTERNAL,
        policy=ErrorPolicy.RETRY,
        retryable=True,
        deterministic=False,
        replay_safe=False,
        degraded=False,
    )


def _invalid_payload() -> ErrorClassification:
    return ErrorClassification(
        kind=ErrorClassificationKind.INVALID_PAYLOAD,
        domain=ErrorDomain.API,
        policy=ErrorPolicy.FAIL_CLOSED,
        retryable=False,
        deterministic=True,
        replay_safe=True,
        degraded=False,
    )
