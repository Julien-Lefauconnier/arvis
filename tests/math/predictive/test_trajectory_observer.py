# tests/math/predictive/test_trajectory_observer.py

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.predictive.trajectory_observer import TrajectoryObserver


def make_state(v):
    return LyapunovState(
        budget_used=v,
        risk=v,
        uncertainty=v,
        governance=v,
    )


def test_trajectory_initial():
    obs = TrajectoryObserver()

    snap = obs.push(make_state(0.2))

    assert snap.window_size == 1
    assert snap.v_max == snap.last_v
    assert snap.drift_pos_sum == 0
    assert snap.verdict == "OK"


def test_trajectory_growth():
    obs = TrajectoryObserver()

    obs.push(make_state(0.2))
    snap = obs.push(make_state(0.4))

    assert snap.v_max >= snap.last_v
    assert snap.drift_pos_sum >= 0


def test_trajectory_bounds():
    obs = TrajectoryObserver()

    obs.push(make_state(0.9))
    snap = obs.push(make_state(1.0))

    assert 0 <= snap.v_max <= 1
    assert 0 <= snap.mean_abs_delta <= 1
