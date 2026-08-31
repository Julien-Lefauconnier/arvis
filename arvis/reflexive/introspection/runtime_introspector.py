# arvis/reflexive/introspection/runtime_introspector.py

from typing import Any


class RuntimeIntrospector:
    def snapshot(self) -> dict[str, Any]:
        return {
            "kind": "static_declaration",
            "mode": "reflexive",
            "runtime": "arvis",
        }
