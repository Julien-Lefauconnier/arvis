# arvis/control/control_signal.py

from dataclasses import dataclass

from .understanding_snapshot import UnderstandingState


@dataclass(frozen=True)
class ControlSignal:
    """
    Minimal control signal for orchestration.
    """

    understanding: UnderstandingState | None
    requires_validation: bool
    autonomy_level: str  # "low", "medium", "high"
