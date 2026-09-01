# tests/fixtures/builders/runtime_builder.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.kernel.pipeline.context.execution_context import (
    PipelineExecutionContext,
)
from arvis.kernel.pipeline.context.runtime_bindings_context import (
    PipelineRuntimeBindingsContext,
)
from arvis.kernel.pipeline.context.scientific_context import (
    PipelineScientificContext,
)


def build_runtime_test_context() -> SimpleNamespace:
    """
    Minimal runtime-compatible context.

    Used for:
    - RuntimeStage tests
    - execution ownership tests
    - runtime binding migration
    - scheduler/runtime integration tests

    Intentionally lightweight and mutable. Carries the canonical
    scientific sub-context so seeds and reads use the same paths as
    the real pipeline context (the root facade mirrors are retired).
    """

    ctx = SimpleNamespace()

    ctx.execution = PipelineExecutionContext()

    ctx.runtime_bindings = PipelineRuntimeBindingsContext()

    ctx.scientific = PipelineScientificContext()

    return ctx
