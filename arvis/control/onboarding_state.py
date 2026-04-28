# arvis/control/onboarding_state.py

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class OnboardingState:
    """
    Declarative onboarding snapshot.
    """

    user_id: str
    data: dict[str, Any]
    initialized_at: datetime
