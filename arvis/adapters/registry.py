# arvis/adapters/registry.py

from typing import Any


def get_llm_adapter(ctx: Any) -> Any | None:
    adapters = getattr(ctx, "extra", {}).get("adapters", {})
    return adapters.get("llm")
