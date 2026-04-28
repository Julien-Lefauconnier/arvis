# arvis/control/control_state.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Set


@dataclass(frozen=True)
class ControlState:
    """
    Declarative snapshot of user control state.

    Kernel invariants:
    - immutable
    - no execution
    """

    user_id: str
    place_id: Optional[str]

    # Action traces
    recent_action_ids: List[str]
    recent_decisions: List[str]

    # Preferences
    preferences: Optional[Dict[str, List[str]]]

    # Cognitive signals (abstracted)
    conflicts: List[str]
    conflict_hints: List[str]

    last_event_at: Optional[datetime]

    # Reasoning
    reasoning_intents: List[str] = field(default_factory=list)

    # Action governance
    allowed_action_modes: Set[str] = field(default_factory=lambda: {"assisted"})
    pending_actions: List[str] = field(default_factory=list)
    audit_actions: List[str] = field(default_factory=list)

    # Visibility
    action_visibility: Dict[str, str] = field(default_factory=dict)
