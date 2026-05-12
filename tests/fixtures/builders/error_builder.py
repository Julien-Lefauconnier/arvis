# tests/fixtures/builders/error_builder.py

from __future__ import annotations

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
) -> ArvisError:
    class SyntheticError(ArvisError):
        pass

    SyntheticError.domain = domain
    SyntheticError.category = category
    SyntheticError.severity = severity
    SyntheticError.policy = policy
    SyntheticError.retryable = retryable
    SyntheticError.deterministic = deterministic
    SyntheticError.replay_safe = replay_safe
    SyntheticError.degraded = degraded

    return SyntheticError(
        message,
        code=code,
        semantics=semantics,
    )
