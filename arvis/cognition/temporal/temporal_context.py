# arvis/cognition/temporal/temporal_context.py

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass(frozen=True)
class TemporalContext:
    """
    Declarative snapshot describing temporal constraints.

    Invariants:
    - immutable
    - serializable
    - no content access
    - no side effects
    """

    last_seen_timestamp: int
    cooldown_seconds: int
    current_timestamp: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)
