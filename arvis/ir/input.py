# arvis/ir/input.py

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CognitiveInputIR:
    """
    Canonical cognitive input (pre-decision).
    """

    input_id: str
    actor_id: str
    surface_kind: str  # linguistic / tool / system / event
    intent_hint: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
