# arvis/cognition/policy/cognitive_signal_snapshot.py

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass(frozen=True)
class CognitiveSignalSnapshot:
    """
    Read-only snapshot representing an exposable cognitive signal.

    Kernel invariants:
    - immutable
    - serializable
    - no raw content
    - no side effects
    """

    signal_id: str
    signal_type: str
    source: str
    timestamp: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)