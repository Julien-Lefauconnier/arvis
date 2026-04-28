# tests/cognition/test_cognitive_state.py

from arvis.cognition.state.cognitive_state import (
    CognitiveControl,
    CognitiveDynamics,
    CognitiveProjection,
    CognitiveRisk,
    CognitiveStability,
    CognitiveState,
)


def _dummy_state():
    return CognitiveState(
        bundle_id="test",
        stability=CognitiveStability(
            dv=0.0,
            regime=None,
            stable=True,
        ),
        risk=CognitiveRisk(
            mh_risk=0.0,
            world_risk=0.0,
            forecast_risk=0.0,
            fused_risk=0.0,
            smoothed_risk=0.0,
            early_warning=False,
        ),
        control=CognitiveControl(
            epsilon=0.0,
        ),
        dynamics=CognitiveDynamics(
            system_tension=None,
            drift=None,
        ),
        projection=CognitiveProjection(
            valid=True,
            margin=0.0,
        ),
        world_prediction=None,
        forecast=None,
        irg=None,
    )


def test_cognitive_state_creation():
    state = _dummy_state()
    assert state.bundle_id == "test"
    assert state.stability.dv == 0.0


def test_cognitive_state_equality():
    s1 = _dummy_state()
    s2 = _dummy_state()
    assert s1 == s2
