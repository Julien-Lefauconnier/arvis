# arvis/adapters/registry.py

from typing import Any, Optional


def get_llm_adapter(ctx: Any) -> Optional[Any]:
    adapters = getattr(ctx, "extra", {}).get("adapters", {})
    return adapters.get("llm")
