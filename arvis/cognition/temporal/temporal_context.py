# arvis/cognition/temporal/temporal_context.py

from dataclasses import asdict, dataclass


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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
