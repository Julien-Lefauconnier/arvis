# tests/errors/test_error_manager.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorCategory,
    ArvisErrorSeverity,
    ErrorDomain,
    ErrorPolicy,
    ErrorSemantics,
)
from arvis.errors.manager import ErrorManager
from tests.fixtures.builders.error_builder import build_error


def test_attach_adds_error(ctx):
    error = build_error()

    payload = ErrorManager.attach(ctx, error)

    assert payload["code"] == "TEST_ERROR"

    assert "errors" in ctx.extra
    assert len(ctx.extra["errors"]) == 1


def test_attach_sets_last_error(ctx):
    error = build_error(code="LAST_ERROR")

    ErrorManager.attach(ctx, error)

    assert ctx.extra["last_error"]["code"] == "LAST_ERROR"


def test_attach_adds_degraded(ctx):
    error = build_error(
        degraded=True,
        severity=ArvisErrorSeverity.WARNING,
        policy=ErrorPolicy.DEGRADE,
    )

    ErrorManager.attach(ctx, error)

    assert ctx.extra["degraded"] == ["TEST_ERROR"]


def test_attach_adds_kernel_failures(ctx):
    error = build_error(
        severity=ArvisErrorSeverity.ERROR,
    )

    ErrorManager.attach(ctx, error)

    assert ctx.extra["kernel_failures"] == ["TEST_ERROR"]


def test_statistics_empty(ctx):
    stats = ErrorManager.statistics(ctx)

    assert stats["total"] == 0
    assert stats["fatal"] == 0


def test_statistics_counts(ctx):
    ErrorManager.attach(
        ctx,
        build_error(),
    )

    ErrorManager.attach(
        ctx,
        build_error(
            degraded=True,
            severity=ArvisErrorSeverity.WARNING,
            policy=ErrorPolicy.DEGRADE,
        ),
    )

    stats = ErrorManager.statistics(ctx)

    assert stats["total"] == 2
    assert stats["error"] == 1
    assert stats["warning"] == 1
    assert stats["degraded"] == 1


def test_statistics_non_deterministic(ctx):
    ErrorManager.attach(
        ctx,
        build_error(
            deterministic=False,
        ),
    )

    stats = ErrorManager.statistics(ctx)

    assert stats["non_deterministic"] == 1


def test_statistics_replay_unsafe(ctx):
    ErrorManager.attach(
        ctx,
        build_error(
            replay_safe=False,
        ),
    )

    stats = ErrorManager.statistics(ctx)

    assert stats["replay_unsafe"] == 1


def test_statistics_fail_closed(ctx):
    ErrorManager.attach(
        ctx,
        build_error(
            policy=ErrorPolicy.FAIL_CLOSED,
        ),
    )

    stats = ErrorManager.statistics(ctx)

    assert stats["fail_closed"] == 1


def test_export_replay_safe(ctx):
    safe_error = build_error(
        code="SAFE",
        replay_safe=True,
    )

    unsafe_error = build_error(
        code="UNSAFE",
        replay_safe=False,
    )

    ErrorManager.attach(ctx, safe_error)
    ErrorManager.attach(ctx, unsafe_error)

    exported = ErrorManager.export_replay_safe(ctx)

    assert len(exported) == 1
    assert exported[0]["code"] == "SAFE"


def test_should_escalate_on_fatal(ctx):
    ErrorManager.attach(
        ctx,
        build_error(
            severity=ArvisErrorSeverity.FATAL,
        ),
    )

    assert ErrorManager.should_escalate(ctx) is True


def test_should_escalate_on_fail_closed(ctx):
    ErrorManager.attach(
        ctx,
        build_error(
            policy=ErrorPolicy.FAIL_CLOSED,
        ),
    )

    assert ErrorManager.should_escalate(ctx) is True


def test_should_not_escalate_by_default(ctx):
    ErrorManager.attach(
        ctx,
        build_error(),
    )

    assert ErrorManager.should_escalate(ctx) is False


def test_clear_resets_error_state(ctx):
    ErrorManager.attach(ctx, build_error())

    ErrorManager.clear(ctx)

    assert "errors" not in ctx.extra
    assert "last_error" not in ctx.extra
    assert "error_statistics" not in ctx.extra


def test_attach_supports_custom_semantics(ctx):
    error = build_error(
        semantics=(
            ErrorSemantics.FAIL_OPEN,
            ErrorSemantics.NON_DETERMINISTIC,
        ),
    )

    ErrorManager.attach(ctx, error)

    exported = ctx.extra["errors"][0]

    assert "fail_open" in exported["semantics"]
    assert "non_deterministic" in exported["semantics"]


def test_capture_exception_preserves_semantics(ctx):
    error = build_error(
        semantics=(
            ErrorSemantics.FAIL_OPEN,
            ErrorSemantics.NON_DETERMINISTIC,
        ),
        domain=ErrorDomain.CORE,
        category=ArvisErrorCategory.RUNTIME,
    )

    payload = ErrorManager.capture_exception(
        ctx,
        error,
        code="UPDATED_ERROR",
        details={"stage": "projection"},
    )

    assert payload["code"] == "UPDATED_ERROR"
    assert payload["details"]["stage"] == "projection"

    semantics = payload["semantics"]

    assert "fail_open" in semantics
    assert "non_deterministic" in semantics


def test_runtime_degradation_tracking(ctx):
    error = build_error(
        degraded=True,
        severity=ArvisErrorSeverity.WARNING,
        policy=ErrorPolicy.DEGRADE,
    )

    ErrorManager.attach(ctx, error)

    runtime = ErrorManager.runtime_degradation_state(ctx)

    assert runtime["active"] is True
    assert runtime["count"] == 1
    assert runtime["last_code"] == "TEST_ERROR"
