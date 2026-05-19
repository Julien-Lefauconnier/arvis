# tests/fixtures/builders/runtime_builder.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.kernel.pipeline.context.execution_context import (
    PipelineExecutionContext,
)
from arvis.kernel.pipeline.context.runtime_bindings_context import (
    PipelineRuntimeBindingsContext,
)


def build_runtime_test_context() -> SimpleNamespace:
    """
    Minimal runtime-compatible context.

    Used for:
    - RuntimeStage tests
    - execution ownership tests
    - runtime binding migration
    - scheduler/runtime integration tests

    Intentionally lightweight and mutable.
    """

    ctx = SimpleNamespace()

    ctx.execution = PipelineExecutionContext()

    ctx.runtime_bindings = PipelineRuntimeBindingsContext()

    return ctx
