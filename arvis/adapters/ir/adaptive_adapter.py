# arvis/adapters/ir/adaptive_adapter.py

from __future__ import annotations

from typing import Any


class AdaptiveIRAdapter:
    @staticmethod
    def from_adaptive(snapshot: Any) -> dict[str, Any] | None:
        if snapshot is None:
            return None

        return {
            "schema_version": "v1",
            "available": bool(getattr(snapshot, "is_available", False)),
            "stability_band": getattr(snapshot, "band", None),
            "veto": bool(getattr(snapshot, "is_unstable", False)),
            "margin": getattr(snapshot, "margin", None),
        }
