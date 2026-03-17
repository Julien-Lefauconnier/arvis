# arvis/cognition/control/temporal_modulation.py

from dataclasses import dataclass


@dataclass(frozen=True)
class TemporalModulation:
    """
    Temporal modulation factors.

    Kernel invariants:
    - no timeline access
    - no computation
    - purely declarative multipliers
    """

    risk_multiplier: float = 1.0
    epsilon_multiplier: float = 1.0