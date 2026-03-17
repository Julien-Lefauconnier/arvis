# arvis/cognition/confirmation/confirmation_result.py

from dataclasses import dataclass
from enum import Enum


class ConfirmationStatus(str, Enum):
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