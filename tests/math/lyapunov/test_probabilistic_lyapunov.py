# tests/math/lyapunov/test_probabilistic_lyapunov.py

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.probabilistic_lyapunov import (
    ProbabilisticLyapunovObserver,
)


def make_state(v):
    return LyapunovState(
        budget_used=v,
        risk=v,
        uncertainty=v,
        governance=v,
    )


def test_probabilistic_observer_basic():
    obs = ProbabilisticLyapunovObserver()

    snap = obs.push(make_state(0.2))

    assert snap.window_size == 1
    assert snap.mean_v >= 0
    assert snap.ucb_v >= 0


def test_probabilistic_observer_accumulates():
    obs = ProbabilisticLyapunovObserver()

    obs.push(make_state(0.2))
    snap = obs.push(make_state(0.3))

    assert snap.window_size == 2
    assert snap.std_v >= 0
