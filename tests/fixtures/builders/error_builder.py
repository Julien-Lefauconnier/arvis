# tests/fixtures/builders/error_builder.py

from __future__ import annotations

from typing import Any

from arvis.errors.base import (
    ArvisError,
    ArvisErrorCategory,
    ArvisErrorSeverity,
    ErrorDomain,
    ErrorPolicy,
    ErrorSemantics,
)


def build_error(
    *,
    message: str = "error",
    code: str = "TEST_ERROR",
    domain: ErrorDomain = ErrorDomain.CORE,
    category: ArvisErrorCategory = ArvisErrorCategory.RUNTIME,
    severity: ArvisErrorSeverity = ArvisErrorSeverity.ERROR,
    policy: ErrorPolicy = ErrorPolicy.HALT_PROCESS,
    retryable: bool = False,
    deterministic: bool = True,
    replay_safe: bool = True,
    degraded: bool = False,
    semantics: tuple[ErrorSemantics, ...] | None = None,
    details: dict[str, Any] | None = None,
) -> ArvisError:
    SyntheticError = type(
        "SyntheticError",
        (ArvisError,),
        {
            "domain": domain,
            "category": category,
            "severity": severity,
            "policy": policy,
            "retryable": retryable,
            "deterministic": deterministic,
            "replay_safe": replay_safe,
            "degraded": degraded,
        },
    )

    return SyntheticError(
        message,
        code=code,
        semantics=semantics,
        details=details,
    )
