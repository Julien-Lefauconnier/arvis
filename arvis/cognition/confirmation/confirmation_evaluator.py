# arvis/cognition/confirmation/confirmation_evaluator.py


from .confirmation_request import ConfirmationRequest
from .confirmation_result import ConfirmationResult, ConfirmationStatus


class ConfirmationEvaluator:
    """
    Stateless evaluator for confirmation logic.
    """

    def evaluate(
        self,
        *,
        request: ConfirmationRequest,
        confirmed: bool,
    ) -> ConfirmationResult:
        return ConfirmationResult(
            request_id=request.request_id,
            status=(
                ConfirmationStatus.CONFIRMED
                if confirmed
                else ConfirmationStatus.REJECTED
            ),
        )
