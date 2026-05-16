# tests/errors/test_llm_boundary.py

from __future__ import annotations

from arvis.errors.base import ArvisRuntimeError
from arvis.errors.boundaries.llm import (
    attach_llm_error,
    capture_llm_contract_failure,
    capture_llm_degraded_failure,
    capture_llm_runtime_failure,
)
from tests.fixtures.builders.context_builder import (
    build_test_context,
)


def test_capture_llm_runtime_failure() -> None:
    ctx = build_test_context()

    capture_llm_runtime_failure(
        ctx,
        RuntimeError("provider timeout"),
        component="LLMExecutor",
        message="LLM runtime failure",
    )

    assert ctx.errors
    assert ctx.errors[-1].details["boundary"] == "llm_runtime"


def test_capture_llm_degraded_failure() -> None:
    ctx = build_test_context()

    capture_llm_degraded_failure(
        ctx,
        RuntimeError("fallback used"),
        component="FallbackExecutor",
        message="LLM degraded mode",
    )

    assert ctx.errors
    assert ctx.errors[-1].details["boundary"] == "llm_degraded"
    assert ctx.errors[-1].details["severity"] == "degraded"


def test_capture_llm_contract_failure() -> None:
    ctx = build_test_context()

    capture_llm_contract_failure(
        ctx,
        RuntimeError("invalid schema"),
        component="StructuredOutputValidator",
        message="LLM contract failure",
    )

    assert ctx.errors
    assert ctx.errors[-1].details["boundary"] == "llm_contract"

    assert ctx.errors[-1].details["severity"] == "contract_violation"


def test_attach_llm_error() -> None:
    ctx = build_test_context()

    error = ArvisRuntimeError("llm explicit attach")

    attach_llm_error(ctx, error)

    assert ctx.errors
    assert ctx.errors[-1] is error
