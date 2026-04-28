# arvis/reflexive/introspection/architecture_introspector.py

from typing import Dict, Any, List

from arvis.reflexive.architecture.arvis_system_architecture import (
    ArvisSystemArchitecture,
)


class ArchitectureIntrospector:
    def describe(self) -> Dict[str, Any]:
        layers = ArvisSystemArchitecture.layers()

        structured_layers: List[Dict[str, Any]] = [
            {
                "name": layer.name,
                "description": layer.description,
                "modules": layer.modules,
            }
            for layer in layers
        ]

        return {
            "name": "architecture",
            "description": (
                "ARVIS is structured as a layered cognitive architecture "
                "with clear separation of responsibilities."
            ),
            "layers": structured_layers,
        }
