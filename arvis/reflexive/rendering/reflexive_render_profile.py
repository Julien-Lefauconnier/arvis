# arvis/reflexive/rendering/reflexive_render_profile.py

from dataclasses import dataclass
from typing import Callable, Dict, Any

from arvis.reflexive.snapshot.reflexive_snapshot import (
    ReflexiveSnapshot,
)


@dataclass(frozen=True)
class ReflexiveRenderProfile:
    """
    Declarative rendering profile for reflexive snapshots.

    - deterministic
    - stateless
    - no cognition
    """

    render_fn: Callable[[ReflexiveSnapshot], Dict[str, Any]]

    def apply(self, snapshot: ReflexiveSnapshot) -> Dict[str, Any]:
        return self.render_fn(snapshot)
