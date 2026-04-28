# arvis/reflexive/introspection/runtime_introspector.py

from typing import Any


class RuntimeIntrospector:
    def snapshot(self) -> dict[str, Any]:
        return {
            "mode": "reflexive",
            "runtime": "arvis",
        }
