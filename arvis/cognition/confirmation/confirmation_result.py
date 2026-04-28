# arvis/cognition/confirmation/confirmation_result.py

from dataclasses import dataclass
from enum import StrEnum


class ConfirmationStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ConfirmationResult:
    """
    Declarative confirmation outcome.
    """

    request_id: str
    status: ConfirmationStatus
