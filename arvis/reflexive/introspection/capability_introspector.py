# arvis/reflexive/introspection/capability_introspector.py

from typing import Any

from arvis.reflexive.capabilities.capability_snapshot_builder import (
    build_capability_snapshot,
)


class CapabilityIntrospector:
    def describe(self) -> dict[str, Any]:
        snapshot = build_capability_snapshot()

        capabilities: list[dict[str, str]] = [
            {
                "key": c.key,
                "description": c.description,
            }
            for c in snapshot.capabilities
        ]

        return {
            "name": "capabilities",
            "description": (
                "ARVIS exposes its internal capabilities "
                "as structured, inspectable components."
            ),
            "capabilities": capabilities,
        }
