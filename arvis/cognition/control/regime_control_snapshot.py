# arvis/cognition/control/regime_control_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class RegimeControlSnapshot:
    """
    Declarative mapping of regime → control behavior.

    Kernel invariants:
    - immutable
    - no policy logic
    """

    mode: str
    exploration_factor: float
    confirmation_bias: float
    epsilon_multiplier: float