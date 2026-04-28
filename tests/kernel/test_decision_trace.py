# tests/kernel/test_decision_trace.py


def test_decision_trace_is_immutable():
    from arvis.kernel.trace.decision_trace import DecisionTrace
    from datetime import datetime

    trace = DecisionTrace(
        timestamp=datetime.utcnow(),
        user_id="user_1",
        gate_result=None,
    )

    import pytest

    with pytest.raises(Exception):
        trace.user_id = "hack"
