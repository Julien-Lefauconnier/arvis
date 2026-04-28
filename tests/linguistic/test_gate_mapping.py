# tests/linguistic/test_gate_mapping.py

import pytest

from arvis.cognition.gate.cognitive_gate_verdict import CognitiveGateVerdict
from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.linguistic.acts.gate_mapping import map_gate_verdict_to_act


def test_gate_abstain_maps_to_abstention():
    act = map_gate_verdict_to_act(
        verdict=CognitiveGateVerdict.ABSTAIN,
        has_decision=False,
    )
    assert act.act_type == LinguisticActType.ABSTENTION


def test_gate_confirmation_maps_to_request_confirmation():
    act = map_gate_verdict_to_act(
        verdict=CognitiveGateVerdict.REQUIRE_CONFIRMATION,
        has_decision=False,
    )
    assert act.act_type == LinguisticActType.REQUEST_CONFIRMATION


def test_gate_allow_with_decision_maps_to_decision():
    act = map_gate_verdict_to_act(
        verdict=CognitiveGateVerdict.ALLOW,
        has_decision=True,
    )
    assert act.act_type == LinguisticActType.DECISION


def test_gate_allow_without_decision_maps_to_information():
    act = map_gate_verdict_to_act(
        verdict=CognitiveGateVerdict.ALLOW,
        has_decision=False,
    )
    assert act.act_type == LinguisticActType.INFORMATION


def test_invalid_verdict_raises():
    class FakeVerdict:
        pass

    with pytest.raises(ValueError):
        map_gate_verdict_to_act(
            verdict=FakeVerdict(),
            has_decision=False,
        )
