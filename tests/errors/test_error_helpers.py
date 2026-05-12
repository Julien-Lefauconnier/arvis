# tests/errors/test_error_helpers.py

from __future__ import annotations

from arvis.errors.helpers import append_error


def test_append_error_adds_error(ctx, runtime_error):
    append_error(ctx, runtime_error)

    assert "errors" in ctx.extra
    assert len(ctx.extra["errors"]) == 1

    payload = ctx.extra["errors"][0]

    assert payload["code"] == "TEST_ERROR"
    assert payload["category"] == "runtime"


def test_append_error_adds_degraded_flag(ctx, degraded_error):
    append_error(ctx, degraded_error)

    assert ctx.extra["degraded"] == ["DEGRADED_MODE"]


def test_append_error_adds_kernel_failures_for_error(ctx, runtime_error):
    append_error(ctx, runtime_error)

    assert ctx.extra["kernel_failures"] == ["TEST_ERROR"]


def test_append_error_adds_kernel_failures_for_fatal(
    ctx,
    invariant_error,
):
    append_error(ctx, invariant_error)

    assert ctx.extra["kernel_failures"] == ["INVARIANT_VIOLATION"]


def test_append_error_does_not_add_kernel_failures_for_warning(
    ctx,
    degraded_error,
):
    append_error(ctx, degraded_error)

    assert "kernel_failures" not in ctx.extra
