# arvis/reflexive/rendering/reflexive_renderer.py

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReflexiveRenderer:
    """
    Stateless rendering wrapper for reflexive snapshots.

    - deterministic
    - pure
    - no cognition
    - no inference
    """

    render_fn: Callable[[Any], dict[str, Any]]

    def apply(self, snapshot: Any) -> dict[str, Any]:
        return self.render_fn(snapshot)

    # Alias de compatibilité (tests + legacy)
    def render(self, snapshot: Any) -> dict[str, Any]:
        result: dict[str, Any] = self.render_fn(snapshot)
        return result
