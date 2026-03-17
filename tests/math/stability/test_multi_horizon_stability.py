# tests/math/stability/test_multi_horizon_stability.py

from arvis.math.stability.multi_horizon_stability import MultiHorizonStabilityObserver


def test_multi_horizon_basic():
    obs = MultiHorizonStabilityObserver()

    snap = obs.evaluate(
        lyapunov_v=0.2,
        trajectory_vmax=0.3,
        predictive_ttc=10,
    )

    assert 0 <= snap.collapse_risk <= 1
    assert 0 <= snap.stability_confidence <= 1
    assert snap.mode_hint == "NORMAL"


def test_multi_horizon_warning():
    obs = MultiHorizonStabilityObserver()

    snap = obs.evaluate(
        lyapunov_v=0.4,
        trajectory_vmax=0.8,
        predictive_ttc=3,
    )

    assert snap.early_warning is True
    assert snap.mode_hint in {"CAUTION", "SAFE"}