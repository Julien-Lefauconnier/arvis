# arvis/cognition/coherence/change_budget.py

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ChangeBudget:
    """
    Declarative snapshot representing a change budget.

    This budget:
    - counts changes
    - does not auto-correct
    - does not optimize
    - does not enforce
    """

    max_changes: int
    current_changes: int
    timestamp: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
