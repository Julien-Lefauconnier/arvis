# arvis/conversation/user_adaptive_profile.py

from typing import Dict


class UserAdaptiveProfile:
    """
    Stores adaptive parameters per user.

    ZKCS-safe:
    - no content
    - no raw memory
    - only abstract signals
    """

    def __init__(self) -> None:
        self.weights: Dict[str, float] = {
            "collapse": 0.5,
            "uncertainty": 0.3,
            "pressure": 0.2,
            "memory": 0.15,
            "constraint": 0.1,
        }

        self.adaptation_count: int = 0
