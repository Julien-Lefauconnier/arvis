# tests/kernel/test_decision_trace.py


def test_decision_trace_is_immutable():
    from arvis.kernel.trace.decision_trace import DecisionTrace
    from arvis.types import utcnow

    trace = DecisionTrace(
        timestamp=utcnow(),
        user_id="user_1",
        gate_result=None,
    )

    import pytest

    with pytest.raises(AttributeError):
        trace.user_id = "hack"
