# arvis/cognition/confirmation/confirmation_request.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfirmationRequest:
    """
    Declarative confirmation requirement.

    Represents a need for external validation.
    """

    request_id: str
    target_id: str
    reason: str
