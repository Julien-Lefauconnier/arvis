# tests/math/predictive/test_predictive_multi_horizon.py

from arvis.math.predictive.predictive_multi_horizon import (
    MultiHorizonPredictiveObserver,
)
from arvis.math.lyapunov.lyapunov import LyapunovState


def make_state(v):
    return LyapunovState(
        budget_used=v,
        risk=v,
        uncertainty=v,
        governance=v,
    )


def test_multi_horizon_initial():
    obs = MultiHorizonPredictiveObserver()

    snap = obs.push(make_state(0.2))

    assert snap.short_v == snap.last_v
    assert snap.medium_v == snap.last_v
    assert snap.long_v == snap.last_v
    assert snap.verdict == "OK"


def test_multi_horizon_prediction_growth():
    obs = MultiHorizonPredictiveObserver()

    obs.push(make_state(0.2))
    snap = obs.push(make_state(0.3))

    assert snap.short_v >= snap.last_v
    assert snap.medium_v >= snap.last_v
    assert snap.long_v >= snap.last_v


def test_multi_horizon_properties():
    obs = MultiHorizonPredictiveObserver()

    obs.push(make_state(0.2))
    snap = obs.push(make_state(0.25))

    assert snap.predicted_v == snap.long_v
    assert snap.horizon == snap.horizons[-1]


def test_multi_horizon_bounds():
    obs = MultiHorizonPredictiveObserver()

    obs.push(make_state(0.9))
    snap = obs.push(make_state(1.0))

    assert 0 <= snap.short_v <= 1
    assert 0 <= snap.medium_v <= 1
    assert 0 <= snap.long_v <= 1
