# arvis/errors/manager.py

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Final, cast

from arvis.errors.base import (
    ArvisError,
    ArvisErrorSeverity,
    ErrorPolicy,
    ErrorSemantics,
)
from arvis.errors.context import ensure_error_extra
from arvis.errors.normalization import normalize_error
from arvis.errors.provenance import ErrorCause, ErrorOrigin, cause_from_exception
from arvis.errors.redaction import redact_error_payload
from arvis.errors.types import ErrorPayload

ERRORS_KEY: Final[str] = "errors"
DEGRADED_KEY: Final[str] = "degraded"
KERNEL_FAILURES_KEY: Final[str] = "kernel_failures"
LAST_ERROR_KEY: Final[str] = "last_error"
ERROR_STATS_KEY: Final[str] = "error_statistics"
RUNTIME_DEGRADATION_KEY: Final[str] = "runtime_degradation"

DEFAULT_DEGRADED_ESCALATION_THRESHOLD: Final[int] = 3
DEFAULT_ERROR_ESCALATION_THRESHOLD: Final[int] = 5


class ErrorManager:
    """
    Centralized error orchestration layer.

    Responsibilities:
    - normalize and attach errors to context-like objects
    - maintain deterministic error counters
    - expose replay-safe error views
    - expose escalation signals

    Non-responsibilities:
    - no retry execution
    - no pipeline control
    - no runtime scheduling
    - no IO
    """

    @staticmethod
    def attach(
        ctx: Any,
        error: ArvisError | Exception,
        *,
        safe: bool = False,
    ) -> ErrorPayload:
        arvis_error = normalize_error(error)
        payload = arvis_error.to_safe_dict() if safe else arvis_error.to_dict()

        extra = ErrorManager._extra(ctx)

        errors = ErrorManager._list(extra, ERRORS_KEY)
        errors.append(payload)

        extra[LAST_ERROR_KEY] = payload

        if arvis_error.degraded:
            degraded = ErrorManager._list(extra, DEGRADED_KEY)
            degraded.append(arvis_error.code)
            runtime = cast(
                dict[str, Any],
                extra.setdefault(
                    RUNTIME_DEGRADATION_KEY,
                    {
                        "active": False,
                        "count": 0,
                        "last_code": None,
                        "domains": {},
                    },
                ),
            )

            runtime["active"] = True
            runtime["count"] = int(runtime.get("count", 0)) + 1
            runtime["last_code"] = arvis_error.code

            domains = cast(dict[str, int], runtime.setdefault("domains", {}))

            domain_key = arvis_error.domain.value

            domains[domain_key] = int(domains.get(domain_key, 0)) + 1

        if arvis_error.severity in {
            ArvisErrorSeverity.ERROR,
            ArvisErrorSeverity.FATAL,
        }:
            failures = ErrorManager._list(extra, KERNEL_FAILURES_KEY)
            failures.append(arvis_error.code)

        ErrorManager._update_statistics(extra, arvis_error)

        return payload

    @staticmethod
    def statistics(ctx: Any) -> dict[str, int]:
        extra = ErrorManager._extra(ctx)
        stats = extra.get(ERROR_STATS_KEY)

        if not isinstance(stats, dict):
            raise TypeError(f"ctx.extra[{ERROR_STATS_KEY!r}] must be a dict")

        return {
            "total": int(stats.get("total", 0)),
            "fatal": int(stats.get("fatal", 0)),
            "error": int(stats.get("error", 0)),
            "warning": int(stats.get("warning", 0)),
            "info": int(stats.get("info", 0)),
            "degraded": int(stats.get("degraded", 0)),
            "retryable": int(stats.get("retryable", 0)),
            "replay_unsafe": int(stats.get("replay_unsafe", 0)),
            "non_deterministic": int(stats.get("non_deterministic", 0)),
            "fail_closed": int(stats.get("fail_closed", 0)),
        }

    @staticmethod
    def runtime_degradation_state(ctx: Any) -> dict[str, Any]:
        extra = ErrorManager._extra(ctx)

        runtime = extra.get(RUNTIME_DEGRADATION_KEY)

        if not isinstance(runtime, dict):
            return {
                "active": False,
                "count": 0,
                "last_code": None,
                "domains": {},
            }

        return {
            "active": bool(runtime.get("active", False)),
            "count": int(runtime.get("count", 0)),
            "last_code": runtime.get("last_code"),
            "domains": dict(runtime.get("domains", {})),
        }

    @staticmethod
    def should_escalate(
        ctx: Any,
        *,
        degraded_threshold: int = DEFAULT_DEGRADED_ESCALATION_THRESHOLD,
        error_threshold: int = DEFAULT_ERROR_ESCALATION_THRESHOLD,
    ) -> bool:
        stats = ErrorManager.statistics(ctx)

        if stats["fatal"] > 0:
            return True

        if stats["degraded"] >= degraded_threshold:
            return True

        if stats["error"] >= error_threshold:
            return True

        if stats["fail_closed"] > 0:
            return True

        return False

    @staticmethod
    def export_replay_safe(ctx: Any) -> list[ErrorPayload]:
        extra = ErrorManager._extra(ctx)
        raw_errors = extra.get(ERRORS_KEY)

        if not isinstance(raw_errors, list):
            return []

        replay_safe: list[ErrorPayload] = []

        for item in raw_errors:
            if not isinstance(item, dict):
                continue

            payload = cast(ErrorPayload, item)
            if payload.get("replay_safe") is True:
                replay_safe.append(redact_error_payload(payload))

        return replay_safe

    @staticmethod
    def last_error(ctx: Any) -> ErrorPayload | None:
        extra = ErrorManager._extra(ctx)
        raw = extra.get(LAST_ERROR_KEY)

        if isinstance(raw, dict):
            return cast(ErrorPayload, raw)

        return None

    @staticmethod
    def clear(ctx: Any) -> None:
        extra = ErrorManager._extra(ctx)

        extra.pop(ERRORS_KEY, None)
        extra.pop(DEGRADED_KEY, None)
        extra.pop(KERNEL_FAILURES_KEY, None)
        extra.pop(LAST_ERROR_KEY, None)
        extra.pop(ERROR_STATS_KEY, None)
        extra.pop(RUNTIME_DEGRADATION_KEY, None)

    @staticmethod
    def _extra(ctx: Any) -> MutableMapping[str, Any]:
        return ensure_error_extra(ctx)

    @staticmethod
    def _list(
        extra: MutableMapping[str, Any],
        key: str,
    ) -> list[Any]:
        value = extra.setdefault(key, [])

        if not isinstance(value, list):
            raise TypeError(f"ctx.extra[{key!r}] must be a list")

        return value

    @staticmethod
    def _update_statistics(
        extra: MutableMapping[str, Any],
        error: ArvisError,
    ) -> None:
        stats = extra.setdefault(ERROR_STATS_KEY, ErrorManager._empty_statistics())

        if not isinstance(stats, dict):
            raise TypeError(f"ctx.extra[{ERROR_STATS_KEY!r}] must be a dict")

        stats["total"] = int(stats.get("total", 0)) + 1
        stats[error.severity.value] = int(stats.get(error.severity.value, 0)) + 1

        if error.degraded:
            stats["degraded"] = int(stats.get("degraded", 0)) + 1

        if error.retryable:
            stats["retryable"] = int(stats.get("retryable", 0)) + 1

        semantics = set(error.metadata.semantics)

        if ErrorSemantics.REPLAY_UNSAFE in semantics:
            stats["replay_unsafe"] = int(stats.get("replay_unsafe", 0)) + 1

        if ErrorSemantics.NON_DETERMINISTIC in semantics:
            stats["non_deterministic"] = int(stats.get("non_deterministic", 0)) + 1

        if error.policy == ErrorPolicy.FAIL_CLOSED:
            stats["fail_closed"] = int(stats.get("fail_closed", 0)) + 1

    @staticmethod
    def _empty_statistics() -> dict[str, int]:
        return {
            "total": 0,
            "fatal": 0,
            "error": 0,
            "warning": 0,
            "info": 0,
            "degraded": 0,
            "retryable": 0,
            "replay_unsafe": 0,
            "non_deterministic": 0,
            "fail_closed": 0,
        }

    @staticmethod
    def capture_exception(
        ctx: Any,
        exc: Exception,
        *,
        code: str | None = None,
        details: dict[str, str | int | float | bool | None] | None = None,
        origin: ErrorOrigin | None = None,
        cause: ErrorCause | None = None,
    ) -> ErrorPayload:
        arvis_error = normalize_error(exc)

        merged_details = dict(arvis_error.details)
        if details:
            merged_details.update(details)

        if (
            code is not None
            or merged_details != arvis_error.details
            or origin is not None
            or cause is not None
        ):
            arvis_error = arvis_error.clone(
                code=code or arvis_error.code,
                details=merged_details,
                origin=origin or arvis_error.origin,
                cause=cause or arvis_error.cause or cause_from_exception(exc),
            )

        return ErrorManager.attach(ctx, arvis_error)

    @staticmethod
    def capture_runtime_degradation(
        ctx: Any,
        exc: Exception,
        *,
        code: str,
        component: str,
    ) -> ErrorPayload:
        return ErrorManager.capture_exception(
            ctx,
            exc,
            code=code,
            origin=ErrorOrigin(component=component, subsystem="runtime"),
            details={
                "component": component,
                "runtime_degraded": True,
            },
        )

    @staticmethod
    def capture_computation_failure(
        ctx: Any,
        exc: Exception,
        *,
        component: str,
    ) -> ErrorPayload:
        return ErrorManager.capture_exception(
            ctx,
            exc,
            code="COMPUTATION_FAILURE",
            origin=ErrorOrigin(component=component, subsystem="computation"),
            details={
                "component": component,
                "computation_failure": True,
            },
        )
