# arvis/action/action_decision.py

from dataclasses import dataclass
from typing import Optional, Any

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
    tool: Optional[str] = None
    tool_payload: Optional[dict[str, Any]] = None
    action_mode: ActionMode = ActionMode.ASSISTED