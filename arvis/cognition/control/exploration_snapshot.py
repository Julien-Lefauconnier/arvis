# arvis/cognition/control/exploration_snapshot.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ExplorationSnapshot:
    """
    Declarative exploration/exploitation configuration.

    Kernel invariants:
    - immutable
    - no execution logic
    - numeric only
    """

    exploration_factor: float
    confirmation_bias: float
    abstain_bias: float
    change_budget_scale: float
    rationale: str