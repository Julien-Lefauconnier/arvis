# tests/fixtures/builders/runtime_bindings_builder.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.context.runtime_bindings_context import (
    PipelineRuntimeBindingsContext,
)


def build_runtime_bindings(
    *,
    runtime: Any | None = None,
    syscall_handler: Any | None = None,
    process_id: str | None = "proc-1",
    run_id: str | None = None,
    adapters: dict[str, Any] | None = None,
) -> PipelineRuntimeBindingsContext:
    return PipelineRuntimeBindingsContext(
        runtime=runtime,
        syscall_handler=syscall_handler,
        process_id=process_id,
        run_id=run_id,
        adapters=adapters or {},
    )
