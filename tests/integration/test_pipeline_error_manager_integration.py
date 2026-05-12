# tests/integration/test_pipeline_error_manager_integration.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisDegradedModeError,
    ArvisRuntimeError,
)
from arvis.errors.manager import ErrorManager
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


def test_error_manager_attaches_runtime_error():
    ctx = CognitivePipelineContext(
        user_id="test-user",
        cognitive_input={"query": "test"},
    )

    error = ArvisRuntimeError(
        "runtime failure",
        code="RUNTIME_FAILURE",
    )

    ErrorManager.attach(ctx, error)

    assert "errors" in ctx.extra
    assert len(ctx.extra["errors"]) == 1

    payload = ctx.extra["errors"][0]

    assert payload["code"] == "RUNTIME_FAILURE"
    assert payload["message"] == "runtime failure"

    assert ctx.extra["kernel_failures"] == ["RUNTIME_FAILURE"]


def test_error_manager_attaches_degraded_error():
    ctx = CognitivePipelineContext(
        user_id="test-user",
        cognitive_input={"query": "test"},
    )

    error = ArvisDegradedModeError(
        "degraded runtime",
        code="DEGRADED_RUNTIME",
    )

    ErrorManager.attach(ctx, error)

    assert "errors" in ctx.extra
    assert len(ctx.extra["errors"]) == 1

    payload = ctx.extra["errors"][0]

    assert payload["code"] == "DEGRADED_RUNTIME"

    assert ctx.extra["degraded"] == ["DEGRADED_RUNTIME"]

    assert "kernel_failures" not in ctx.extra


def test_error_manager_keeps_error_order():
    ctx = CognitivePipelineContext(
        user_id="test-user",
        cognitive_input={"query": "test"},
    )

    ErrorManager.attach(
        ctx,
        ArvisRuntimeError(
            "first",
            code="FIRST_ERROR",
        ),
    )

    ErrorManager.attach(
        ctx,
        ArvisRuntimeError(
            "second",
            code="SECOND_ERROR",
        ),
    )

    errors = ctx.extra["errors"]

    assert errors[0]["code"] == "FIRST_ERROR"
    assert errors[1]["code"] == "SECOND_ERROR"


def test_error_manager_is_append_only():
    ctx = CognitivePipelineContext(
        user_id="test-user",
        cognitive_input={"query": "test"},
    )

    ctx.extra["custom"] = {
        "preserved": True,
    }

    ErrorManager.attach(
        ctx,
        ArvisRuntimeError(
            "runtime",
            code="RUNTIME_ERROR",
        ),
    )

    assert ctx.extra["custom"] == {
        "preserved": True,
    }


def test_error_manager_preserves_serializable_payload():
    ctx = CognitivePipelineContext(
        user_id="test-user",
        cognitive_input={"query": "test"},
    )

    error = ArvisRuntimeError(
        "runtime",
        code="SERIALIZATION_TEST",
        details={
            "stage": "gate",
            "retry_count": 2,
        },
    )

    ErrorManager.attach(ctx, error)

    payload = ctx.extra["errors"][0]

    assert payload["details"] == {
        "stage": "gate",
        "retry_count": 2,
    }
