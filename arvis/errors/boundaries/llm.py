# arvis/errors/boundaries/llm.py

from __future__ import annotations

from typing import Any

from arvis.errors.base import ArvisError
from arvis.errors.manager import ErrorManager


def capture_llm_runtime_failure(
    ctx: Any,
    exc: Exception,
    *,
    component: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    ErrorManager.capture_exception(
        ctx,
        exc,
        details={
            "boundary": "llm_runtime",
            "component": component,
            "message": message,
            **(details or {}),
        },
    )


def capture_llm_degraded_failure(
    ctx: Any,
    exc: Exception,
    *,
    component: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    ErrorManager.capture_exception(
        ctx,
        exc,
        details={
            "boundary": "llm_degraded",
            "severity": "degraded",
            "component": component,
            "message": message,
            **(details or {}),
        },
    )


def capture_llm_contract_failure(
    ctx: Any,
    exc: Exception,
    *,
    component: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    ErrorManager.capture_exception(
        ctx,
        exc,
        details={
            "boundary": "llm_contract",
            "severity": "contract_violation",
            "component": component,
            "message": message,
            **(details or {}),
        },
    )


def attach_llm_error(
    ctx: Any,
    error: ArvisError,
) -> None:
    ErrorManager.attach(ctx, error)
