# tests/stability/test_stability_state_projector.py

from arvis.stability.stability_state_projector import StabilityStateProjector


class Dummy:
    pass


def make_bundle(
    current=0,
    maxc=1,
    conflicts=None,
    frames=None,
    gaps=None,
):
    bundle = Dummy()

    # explanation
    explanation = Dummy()
    explanation.stability = {
        "current_changes": current,
        "max_changes": maxc,
    }
    bundle.explanation = explanation

    # decision_result
    dr = Dummy()
    dr.conflicts = conflicts or []
    dr.uncertainty_frames = frames or []
    dr.gaps = gaps or []

    bundle.decision_result = dr

    return bundle


def test_projector_basic():
    bundle = make_bundle(
        current=2,
        maxc=4,
        conflicts=[1, 2],
        frames=[1],
        gaps=[1, 2, 3],
    )

    state = StabilityStateProjector.from_bundle(bundle)

    assert 0.0 <= state.budget_used <= 1.0
    assert 0.0 <= state.risk <= 1.0
    assert 0.0 <= state.uncertainty <= 1.0
    assert 0.0 <= state.governance <= 1.0


def test_projector_missing_fields_safe():
    bundle = Dummy()
    bundle.explanation = Dummy()
    bundle.decision_result = Dummy()

    state = StabilityStateProjector.from_bundle(bundle)

    assert state.budget_used == 0.0
    assert state.risk == 0.0
    assert state.uncertainty == 0.0
    assert state.governance == 0.0


def test_project_identity():
    proj = StabilityStateProjector()
    obj = {"x": 1}

    assert proj.project(obj) is obj