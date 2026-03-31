# arvis/reflexive/introspection/cognition_introspector.py

from typing import Dict, Any

from arvis.reflexive.architecture.arvis_system_architecture import (
    ArvisSystemArchitecture
)

class CognitionIntrospector:
    """
    Exposes a structured explanation of ARVIS cognition layer.
    """

    def describe(self)-> Dict[str, Any]:

        layers = ArvisSystemArchitecture.layers()

        cognition_layer = next(
            (layer for layer in layers if layer.name == "cognition"),
            None
        )

        if cognition_layer is None:
            return {}

        return {
            "name": cognition_layer.name,
            "description": cognition_layer.description,
            "modules": cognition_layer.modules,
        }