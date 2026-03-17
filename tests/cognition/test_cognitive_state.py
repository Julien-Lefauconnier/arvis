# tests/cognition/test_cognitive_state.py

from arvis.cognition.state.cognitive_state import CognitiveState


def _dummy_state():

    return CognitiveState(
        bundle_id="test",
        dv=0.0,
        collapse_risk=0.0,
        world_prediction=None,
        forecast=None,
        irg=None,
        epsilon=0.0,
        early_warning=False,
    )


def test_cognitive_state_creation():

    state = _dummy_state()

    assert state.bundle_id == "test"


def test_cognitive_state_equality():

    s1 = _dummy_state()
    s2 = _dummy_state()

    assert s1 == s2