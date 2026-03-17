# arvis/control/control_preferences.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass(frozen=True)
class ControlPreferences:
    """
    Declarative user preferences.
    """

    user_id: str
    place_id: Optional[str]

    always_require_validation_for: List[str]
    never_allow_actions: List[str]

    created_at: datetime
    updated_at: datetime

    allowed_action_modes: Optional[List[str]] = None