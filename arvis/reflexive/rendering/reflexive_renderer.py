# arvis/reflexive/rendering/reflexive_renderer.py

from dataclasses import dataclass
from typing import Callable, Any, Dict


@dataclass(frozen=True)
class ReflexiveRenderer:
    """
    Stateless rendering wrapper for reflexive snapshots.

    - deterministic
    - pure
    - no cognition
    - no inference
    """

    render_fn: Callable[[Any], Dict[str, Any]]

    def apply(self, snapshot: Any) -> Dict[str, Any]:
        return self.render_fn(snapshot)

    # Alias de compatibilité (tests + legacy)
    def render(self, snapshot: Any) -> Dict[str, Any]:
        result: Dict[str, Any] = self.render_fn(snapshot)
        return result