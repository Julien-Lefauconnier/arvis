# arvis/kernel/pipeline/context/tooling_accessors.py

"""Duck-tolerant canonical access to the tooling domain.

Campaign OBS (LOT O4). The root context mirrors (_tool_success,
_tool_failure, _last_tool_spec) are retired; the tools layer operates
on partial duck contexts by contract, so writes and reads go through
this installer accessor, mirroring the scientific() pattern.
"""

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.context.tooling_context import (
    PipelineToolingContext,
)


def tooling(ctx: Any) -> PipelineToolingContext:
    runtime = getattr(ctx, "tooling", None)

    if runtime is None:
        runtime = PipelineToolingContext()
        ctx.tooling = runtime
    elif not isinstance(runtime, PipelineToolingContext):
        raise TypeError("ctx.tooling must be a PipelineToolingContext")

    return runtime
