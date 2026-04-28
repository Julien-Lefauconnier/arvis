# tests/stability/test_stability_state_projector.py

import pytest
from arvis.stability.stability_state_projector import StabilityStateProjector
from arvis.math.lyapunov.lyapunov import LyapunovState


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


# ============================================================
# Helpers
# ============================================================


class DummyBundle:
    def __init__(self, explanation=None, decision_result=None):
        self.explanation = explanation
        self.decision_result = decision_result


class DummyExplanation:
    def __init__(self, stability):
        self.stability = stability


class DummyDecision:
    def __init__(self, conflicts=None, uncertainty_frames=None, gaps=None):
        self.conflicts = conflicts
        self.uncertainty_frames = uncertainty_frames
        self.gaps = gaps


# ============================================================
# 1. FULL NORMAL CASE
# ============================================================


def test_full_projection():
    bundle = DummyBundle(
        explanation=DummyExplanation(
            stability={"current_changes": 2, "max_changes": 4}
        ),
        decision_result=DummyDecision(
            conflicts=[1, 2],
            uncertainty_frames=[1],
            gaps=[1, 2, 3],
        ),
    )

    state = StabilityStateProjector.from_bundle(bundle)

    assert isinstance(state, LyapunovState)
    assert 0 < state.budget_used <= 1
    assert state.risk == pytest.approx(2 / 5)
    assert state.uncertainty == pytest.approx(1 / 5)
    assert state.governance == pytest.approx(3 / 5)


# ============================================================
# 2. MISSING FIELDS → SAFE DEFAULTS
# ============================================================


def test_missing_fields():
    bundle = DummyBundle()

    state = StabilityStateProjector.from_bundle(bundle)

    assert state.budget_used == 0.0
    assert state.risk == 0.0
    assert state.uncertainty == 0.0
    assert state.governance == 0.0


# ============================================================
# 3. CLAMP ≥ 5 → 1.0
# ============================================================


def test_clamping():
    bundle = DummyBundle(
        explanation=DummyExplanation(
            stability={"current_changes": 10, "max_changes": 1}
        ),
        decision_result=DummyDecision(
            conflicts=list(range(10)),
            uncertainty_frames=list(range(10)),
            gaps=list(range(10)),
        ),
    )

    state = StabilityStateProjector.from_bundle(bundle)

    assert state.risk == 1.0
    assert state.uncertainty == 1.0
    assert state.governance == 1.0


# ============================================================
# 4. EXCEPTION IN BUDGET
# ============================================================


def test_budget_exception(monkeypatch):
    class Broken:
        def get(self, *a, **k):
            raise ValueError

    bundle = DummyBundle(explanation=DummyExplanation(Broken()))

    state = StabilityStateProjector.from_bundle(bundle)

    assert state.budget_used == 0.0


# ============================================================
# 5. EXCEPTION IN CONFLICTS
# ============================================================


def test_conflicts_exception():
    class BrokenDecision:
        @property
        def conflicts(self):
            raise ValueError

    bundle = DummyBundle(decision_result=BrokenDecision())

    state = StabilityStateProjector.from_bundle(bundle)

    assert state.risk == 0.0


# ============================================================
# 6. EXCEPTION IN UNCERTAINTY
# ============================================================


def test_uncertainty_exception():
    class BrokenDecision:
        @property
        def uncertainty_frames(self):
            raise ValueError

    bundle = DummyBundle(decision_result=BrokenDecision())

    state = StabilityStateProjector.from_bundle(bundle)

    assert state.uncertainty == 0.0


# ============================================================
# 7. EXCEPTION IN GAPS
# ============================================================


def test_gaps_exception():
    class BrokenDecision:
        @property
        def gaps(self):
            raise ValueError

    bundle = DummyBundle(decision_result=BrokenDecision())

    state = StabilityStateProjector.from_bundle(bundle)

    assert state.governance == 0.0


# ============================================================
# 8. PROJECT PASSTHROUGH
# ============================================================


def test_project_passthrough():
    projector = StabilityStateProjector()

    obj = {"test": 123}

    out = projector.project(obj)

    assert out is obj
