# tests/math/stability/test_global_stability.py

from types import SimpleNamespace

from arvis.math.stability.global_stability import GlobalStabilityFusion
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.stability.regime_estimator import RegimeSnapshot


def test_global_stability_basic():

    fusion = GlobalStabilityFusion()

    state = LyapunovState(
        budget_used=0.1,
        risk=0.2,
        uncertainty=0.2,
        governance=0.1,
    )

    predictive = SimpleNamespace(
        predicted_v=0.2,
        slope=0.01,
        horizon=10,
        window_size=50,
    )

    trajectory = SimpleNamespace(
        drift_pos_sum=0.2,
        v_max=0.3,
        mean_abs_delta=0.05,
    )

    probabilistic = SimpleNamespace(
        ucb_v=0.2
    )

    regime = RegimeSnapshot(
        regime="stable",
        confidence=0.9,
        variance=0.01,
    )

    snap = fusion.compute(
        state=state,
        predictive=predictive,
        trajectory=trajectory,
        probabilistic=probabilistic,
        regime=regime,
    )

    assert 0 <= snap.global_risk <= 1
    assert snap.regime == "stable"
    assert snap.verdict in {"OK", "WARN", "CRITICAL"}