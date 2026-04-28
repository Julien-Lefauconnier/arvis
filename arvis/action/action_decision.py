# arvis/action/action_decision.py

from dataclasses import dataclass
from typing import Any

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
    denied_reason: str | None = None
    audit_required: bool = False
    tool: str | None = None
    tool_payload: dict[str, Any] | None = None
    action_mode: ActionMode = ActionMode.ASSISTED
