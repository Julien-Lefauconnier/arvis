# tests/math/predictive/test_predictive_stability.py

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.predictive.predictive_stability import PredictiveStabilityObserver


def make_state(v):
    return LyapunovState(
        budget_used=v,
        risk=v,
        uncertainty=v,
        governance=v,
    )


def test_predictive_initial_state():
    obs = PredictiveStabilityObserver()

    snap = obs.push(make_state(0.2))

    assert snap.slope == 0.0
    assert snap.predicted_v == snap.last_v
    assert snap.time_to_critical is None
    assert snap.verdict == "OK"


def test_predictive_positive_slope():
    obs = PredictiveStabilityObserver()

    obs.push(make_state(0.2))
    snap = obs.push(make_state(0.3))

    assert snap.slope > 0
    assert snap.predicted_v >= snap.last_v


def test_predictive_ttc():
    obs = PredictiveStabilityObserver()

    obs.push(make_state(0.6))
    snap = obs.push(make_state(0.7))

    assert snap.slope > 0
    assert snap.time_to_critical is not None


def test_predictive_clamping():
    obs = PredictiveStabilityObserver()

    obs.push(make_state(0.9))
    snap = obs.push(make_state(1.0))

    assert 0 <= snap.predicted_v <= 1
