# arvis/errors/factories.py

from __future__ import annotations

from arvis.errors.base import ArvisError, ErrorDomain
from arvis.errors.manager import ErrorManager


def build_llm_retryable_error(
    message: str,
    *,
    code: str,
    retry_class: str,
) -> ArvisError:
    return ErrorManager.normalize_for_boundary(
        RuntimeError(message),
        boundary="external",
        code=code,
        domain=ErrorDomain.LLM,
        details={
            "retry_class": retry_class,
        },
    )


def build_llm_fatal_error(
    message: str,
    *,
    code: str,
) -> ArvisError:
    return ErrorManager.normalize_for_boundary(
        RuntimeError(message),
        boundary="runtime",
        code=code,
        domain=ErrorDomain.LLM,
        details={
            "retry_class": "fatal",
        },
    )
