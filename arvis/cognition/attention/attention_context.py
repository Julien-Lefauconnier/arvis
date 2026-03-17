# arvis/cognition/attention/attention_context.py

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass(frozen=True)
class AttentionContext:
    """
    Declarative snapshot describing the current attention load.

    Invariants:
    - immutable
    - serializable
    - no content access
    - no side effects
    """

    max_items: int
    current_load: int
    timestamp: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)
