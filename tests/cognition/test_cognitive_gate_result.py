# tests/cognition/test_cognitive_gate_result.py

from arvis.cognition.gate import CognitiveGateResult
from arvis.cognition.gate import CognitiveGateVerdict


def test_gate_result_is_immutable():

    result = CognitiveGateResult(
        verdict=CognitiveGateVerdict.ALLOW,
        reason="ok",
        bundle_id="abc",
    )

    assert result.verdict == CognitiveGateVerdict.ALLOW