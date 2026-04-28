# arvis/reflexive/introspection/uncertainty_introspector.py

from typing import Dict, Any, List, cast

from arvis.uncertainty.uncertainty_frame_registry import (
    UncertaintyFrameRegistry,
)


class UncertaintyIntrospector:
    def describe(self) -> Dict[str, Any]:
        raw_frames = cast(List[Any], UncertaintyFrameRegistry.all())

        frames: List[Dict[str, Any]] = [
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
