# tests/contracts/test_cognitive_state_contract.py

from arvis.cognition.state.cognitive_state import (
    CognitiveState,
    CognitiveStability,
    CognitiveRisk,
    CognitiveControl,
    CognitiveDynamics,
)

from arvis.contracts.cognitive_state_contract import CognitiveStateContract


def test_valid_state_passes():
    state = CognitiveState(
        bundle_id="test",
        stability=CognitiveStability(0.1, "neutral", True),
        risk=CognitiveRisk(0.1, 0.2, 0.3, 0.4, 0.4, False),
        control=CognitiveControl(0.5),
        dynamics=CognitiveDynamics(None, None),
        projection=None,
        world_prediction=None,
        forecast=None,
        irg=None,
    )

    CognitiveStateContract.validate(state)