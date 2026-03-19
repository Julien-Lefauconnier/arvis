# tests/api/test_trace_view.py

from datetime import datetime

from arvis.api.trace import DecisionTraceView
from arvis.kernel.trace.decision_trace import DecisionTrace


class Dummy:
    def __str__(self):
        return "dummy"


def build_minimal_trace():
    return DecisionTrace(
        timestamp=datetime.utcnow(),
        user_id="user-1",
        gate_result=Dummy(),
    )


def test_trace_view_basic():
    trace = build_minimal_trace()

    view = DecisionTraceView.from_trace(trace)

    assert view.user_id == "user-1"
    assert view.decision is None
    assert view.confirmation_required is False


def test_trace_view_to_dict():
    trace = build_minimal_trace()

    view = DecisionTraceView.from_trace(trace)
    d = view.to_dict()

    assert "timestamp" in d
    assert "user_id" in d
    assert "decision" in d

    assert "gate" in d
    assert "confirmation" in d
    assert "observability" in d
    assert "flags" in d


def test_trace_view_summary():
    trace = build_minimal_trace()

    view = DecisionTraceView.from_trace(trace)
    s = view.summary()

    assert "Decision" in s
    assert "Gate" in s

def test_trace_view_with_confirmation():
    class Confirmation:
        confirmed = True

    trace = DecisionTrace(
        timestamp=datetime.utcnow(),
        user_id="user-1",
        gate_result=Dummy(),
        confirmation_request=Dummy(),
        confirmation_result=Confirmation(),
    )

    view = DecisionTraceView.from_trace(trace)

    assert view.confirmation_required is True
    assert view.confirmation_granted is True