# arvis/control/onboarding_state.py

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass(frozen=True)
class OnboardingState:
    """
    Declarative onboarding snapshot.
    """

    user_id: str
    data: Dict[str, Any]
    initialized_at: datetime