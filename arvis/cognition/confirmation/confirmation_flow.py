# arvis/cognition/confirmation/confirmation_flow.py

from dataclasses import dataclass
from typing import Optional

from .confirmation_request import ConfirmationRequest
from .confirmation_result import ConfirmationResult, ConfirmationStatus


@dataclass(frozen=True)
class ConfirmationFlowState:
    """
    Tracks confirmation lifecycle.
    """

    request: ConfirmationRequest
    result: Optional[ConfirmationResult] = None

    @property
    def status(self) -> ConfirmationStatus:
        if self.result is None:
            return ConfirmationStatus.PENDING
        return self.result.status

    @property
    def is_confirmed(self) -> bool:
        return self.status == ConfirmationStatus.CONFIRMED

    @property
    def is_rejected(self) -> bool:
        return self.status == ConfirmationStatus.REJECTED

    @property
    def is_pending(self) -> bool:
        return self.status == ConfirmationStatus.PENDING