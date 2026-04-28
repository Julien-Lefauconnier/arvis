# arvis/reflexive/introspection/uncertainty_introspector.py

from typing import Any, cast

from arvis.uncertainty.uncertainty_frame_registry import (
    UncertaintyFrameRegistry,
)


class UncertaintyIntrospector:
    def describe(self) -> dict[str, Any]:
        raw_frames = cast(list[Any], UncertaintyFrameRegistry.all())

        frames: list[dict[str, Any]] = [
            {
                "id": getattr(f, "frame_id", None),
                "label": getattr(f, "label", None),
                "description": getattr(f, "description", None),
            }
            for f in raw_frames
        ]

        return {
            "name": "uncertainty_system",
            "description": (
                "ARVIS exposes structured uncertainty frames "
                "to make reasoning limits explicit."
            ),
            "frames": frames,
        }
