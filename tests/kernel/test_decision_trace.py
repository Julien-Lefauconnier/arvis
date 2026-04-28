# tests/kernel/test_decision_trace.py


def test_decision_trace_is_immutable():
    from datetime import datetime

    from arvis.kernel.trace.decision_trace import DecisionTrace

    trace = DecisionTrace(
        timestamp=datetime.utcnow(),
        user_id="user_1",
        gate_result=None,
    )

    import pytest

    with pytest.raises(AttributeError):
        trace.user_id = "hack"
