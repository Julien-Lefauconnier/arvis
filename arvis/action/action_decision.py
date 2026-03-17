# arvis/action/action_decision.py

from dataclasses import dataclass
from typing import Optional

from .action_mode import ActionMode


@dataclass(frozen=True)
class ActionDecision:
    """
    Declarative result of evaluating an action.

    Kernel invariants:
    - immutable
    - no execution
    - explicit decision surface
    """

    allowed: bool
    requires_user_validation: bool = False
    denied_reason: Optional[str] = None
    audit_required: bool = False
    action_mode: ActionMode = ActionMode.ASSISTED