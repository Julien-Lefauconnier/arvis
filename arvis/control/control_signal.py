# arvis/control/control_signal.py

from dataclasses import dataclass
from typing import Optional

from .understanding_snapshot import UnderstandingState


@dataclass(frozen=True)
class ControlSignal:
    """
    Minimal control signal for orchestration.
    """

    understanding: Optional[UnderstandingState]
    requires_validation: bool
    autonomy_level: str  # "low", "medium", "high"
