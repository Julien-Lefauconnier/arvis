# tests/ir/test_ir_models.py

from dataclasses import FrozenInstanceError

import pytest

from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR
from arvis.ir.state import CognitiveRiskIR, CognitiveStateIR


def test_decision_ir_is_frozen() -> None:
    decision = CognitiveDecisionIR(
        decision_id="d1",
        decision_kind="informational",
        memory_intent="none",
    )

    with pytest.raises(FrozenInstanceError):
        decision.decision_kind = "action"  # type: ignore[misc]


def test_gate_ir_is_frozen() -> None:
    gate = CognitiveGateIR(
        verdict=CognitiveGateVerdictIR.ALLOW,
        bundle_id="b1",
        reason_codes=("informational_query",),
    )

    with pytest.raises(FrozenInstanceError):
        gate.bundle_id = "b2"  # type: ignore[misc]


def test_state_ir_is_frozen() -> None:
    state = CognitiveStateIR(
        state_id="s1",
        bundle_id="b1",
        dv=0.1,
        collapse_risk=CognitiveRiskIR(
            mh_risk=0.1,
            world_risk=0.2,
            forecast_risk=0.3,
            fused_risk=0.4,
            smoothed_risk=0.5,
        ),
        epsilon=0.2,
        early_warning=False,
    )

    with pytest.raises(FrozenInstanceError):
        state.epsilon = 0.9  # type: ignore[misc]
