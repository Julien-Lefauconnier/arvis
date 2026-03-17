# arvis/action/action_template.py

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ActionTemplate:
    """
    Declarative description of a possible action.

    Kernel invariants:
    - immutable
    - no execution
    - no side effects
    - capability description only
    """

    action_id: str
    description: str

    reads_data: bool = False
    writes_data: bool = False
    triggers_external: bool = False

    risk_level: str = "low"
    reversible: bool = True

    user_facing_label: Optional[str] = None