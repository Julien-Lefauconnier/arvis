# # arvis/tools/runtime/runtime_bindings.py

from __future__ import annotations

from typing import Any


def resolve_process_id(ctx: Any) -> str:
    runtime_bindings = getattr(ctx, "runtime_bindings", None)

    process_id = getattr(runtime_bindings, "process_id", None)

    if isinstance(process_id, str):
        return process_id

    return "unknown"
