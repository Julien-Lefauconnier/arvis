# arvis/control/control_state.py

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ControlState:
    """
    Declarative snapshot of user control state.

    Kernel invariants:
    - immutable
    - no execution
    """

    user_id: str
    place_id: str | None

    # Action traces
    recent_action_ids: list[str]
    recent_decisions: list[str]

    # Preferences
    preferences: dict[str, list[str]] | None

    # Cognitive signals (abstracted)
    conflicts: list[str]
    conflict_hints: list[str]

    last_event_at: datetime | None

    # Reasoning
    reasoning_intents: list[str] = field(default_factory=list)

    # Action governance
    allowed_action_modes: set[str] = field(default_factory=lambda: {"assisted"})
    pending_actions: list[str] = field(default_factory=list)
    audit_actions: list[str] = field(default_factory=list)

    # Visibility
    action_visibility: dict[str, str] = field(default_factory=dict)
