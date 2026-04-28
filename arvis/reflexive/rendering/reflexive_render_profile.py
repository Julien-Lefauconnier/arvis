# arvis/reflexive/rendering/reflexive_render_profile.py

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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

    render_fn: Callable[[ReflexiveSnapshot], dict[str, Any]]

    def apply(self, snapshot: ReflexiveSnapshot) -> dict[str, Any]:
        return self.render_fn(snapshot)
