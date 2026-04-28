# arvis/control/control_preferences.py

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ControlPreferences:
    """
    Declarative user preferences.
    """

    user_id: str
    place_id: str | None

    always_require_validation_for: list[str]
    never_allow_actions: list[str]

    created_at: datetime
    updated_at: datetime

    allowed_action_modes: list[str] | None = None
