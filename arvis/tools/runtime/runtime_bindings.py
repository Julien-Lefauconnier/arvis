# # arvis/tools/runtime/runtime_bindings.py

from __future__ import annotations

from typing import Any


def resolve_process_id(ctx: Any) -> str:
    runtime_bindings = getattr(ctx, "runtime_bindings", None)

    process_id = getattr(runtime_bindings, "process_id", None)

    if isinstance(process_id, str) and process_id:
        return process_id

    return "unknown"


def resolve_run_id(ctx: Any) -> str | None:
    runtime_bindings = getattr(ctx, "runtime_bindings", None)
    run_id = getattr(runtime_bindings, "run_id", None)
    return run_id if isinstance(run_id, str) and run_id else None
