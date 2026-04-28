# tests/cognition/test_cognitive_gate_result.py

from arvis.cognition.gate import CognitiveGateResult, CognitiveGateVerdict
from arvis.cognition.gate.gate_decision_trace import (
    GateDecisionTrace,
    GateDecisionTraceStep,
)


def test_gate_result_is_immutable():
    result = CognitiveGateResult(
        verdict=CognitiveGateVerdict.ALLOW,
        reason_codes=("ok",),
        bundle_id="abc",
    )

    assert result.verdict == CognitiveGateVerdict.ALLOW
    assert result.reason_codes == ("ok",)


def test_gate_result_accepts_decision_trace():
    trace = GateDecisionTrace(
        steps=(
            GateDecisionTraceStep(
                stage="projection_hard_block",
                before="ALLOW",
                after="ABSTAIN",
                reason_codes=("projection_invalid",),
            ),
        )
    )

    result = CognitiveGateResult(
        verdict=CognitiveGateVerdict.ABSTAIN,
        reason_codes=("projection_invalid",),
        bundle_id="abc",
        decision_trace=trace,
    )

    assert result.decision_trace is trace
    assert result.reason_codes == ("projection_invalid",)
