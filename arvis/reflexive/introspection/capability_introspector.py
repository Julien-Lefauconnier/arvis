# arvis/reflexive/introspection/capability_introspector.py

from typing import Dict, Any, List

from arvis.reflexive.capabilities.capability_snapshot_builder import (
    build_capability_snapshot
)


class CapabilityIntrospector:

    def describe(self) -> Dict[str, Any]:

        snapshot = build_capability_snapshot()

        capabilities: List[Dict[str, str]] = [
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