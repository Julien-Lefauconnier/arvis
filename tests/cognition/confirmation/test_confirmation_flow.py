# tests/cognition/confirmation/test_confirmation_flow.py

from arvis.cognition.confirmation.confirmation_flow import ConfirmationFlowState
from arvis.cognition.confirmation.confirmation_request import ConfirmationRequest
from arvis.cognition.confirmation.confirmation_result import (
    ConfirmationResult,
    ConfirmationStatus,
)


def make_request():
    return ConfirmationRequest(
        request_id="req1",
        target_id="target",
        reason="test",
    )


def test_flow_initial_state_pending():
    flow = ConfirmationFlowState(request=make_request())

    assert flow.is_pending is True
    assert flow.is_confirmed is False
    assert flow.is_rejected is False


def test_flow_confirmed():
    flow = ConfirmationFlowState(
        request=make_request(),
        result=ConfirmationResult(
            request_id="req1",
            status=ConfirmationStatus.CONFIRMED,
        ),
    )

    assert flow.is_confirmed is True
    assert flow.is_pending is False


def test_flow_rejected():
    flow = ConfirmationFlowState(
        request=make_request(),
        result=ConfirmationResult(
            request_id="req1",
            status=ConfirmationStatus.REJECTED,
        ),
    )

    assert flow.is_rejected is True
    assert flow.is_pending is False


def test_flow_status_property():
    flow = ConfirmationFlowState(request=make_request())
    assert flow.status == ConfirmationStatus.PENDING

    flow = ConfirmationFlowState(
        request=make_request(),
        result=ConfirmationResult(
            request_id="req1",
            status=ConfirmationStatus.CONFIRMED,
        ),
    )
    assert flow.status == ConfirmationStatus.CONFIRMED
