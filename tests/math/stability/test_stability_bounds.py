# tests/math/stability/test_stability_bounds.py

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.predictive.predictive_stability import PredictiveSnapshot
from arvis.math.predictive.trajectory_observer import TrajectorySnapshot
from arvis.math.stability.global_stability import (
    GlobalStabilityFusion,
    GlobalStabilitySnapshot,
)
from arvis.math.stability.hybrid_risk_observer import HybridRiskObserver
from arvis.math.stability.multi_horizon_stability import MultiHorizonStabilityObserver


def test_hybrid_risk_output_bounds():
    snap = HybridRiskObserver.fuse(
        v_numeric=0.2,
        v_symbolic=0.4,
    )

    assert 0.0 <= snap.v_numeric <= 1.0
    assert 0.0 <= snap.v_symbolic <= 1.0
    assert 0.0 <= snap.p_numeric <= 1.0
    assert 0.0 <= snap.p_symbolic <= 1.0
    assert 0.0 <= snap.collapse_risk <= 1.0


def test_multi_horizon_output_bounds():
    obs = MultiHorizonStabilityObserver()

    snap = obs.evaluate(
        lyapunov_v=0.2,
        trajectory_vmax=0.3,
        predictive_ttc=8,
    )

    assert 0.0 <= snap.collapse_risk <= 1.0
    assert 0.0 <= snap.stability_confidence <= 1.0


def test_global_stability_output_bounds():
    fusion = GlobalStabilityFusion()

    state = LyapunovState(
        budget_used=0.1,
        risk=0.2,
        uncertainty=0.2,
        governance=0.1,
    )

    predictive = PredictiveSnapshot(
        window_size=5,
        horizon=10,
        last_v=0.2,
        slope=0.01,
        predicted_v=0.3,
        time_to_critical=None,
        verdict="OK",
    )

    trajectory = TrajectorySnapshot(
        window_size=5,
        last_v=0.2,
        v_max=0.3,
        drift_pos_sum=0.1,
        mean_abs_delta=0.05,
        verdict="OK",
    )

    class _Prob:
        ucb_v = 0.25

    snap = fusion.compute(
        state=state,
        predictive=predictive,
        trajectory=trajectory,
        probabilistic=_Prob(),
        regime=None,
    )

    assert isinstance(snap, GlobalStabilitySnapshot)
    assert 0.0 <= snap.global_risk <= 1.0
    assert snap.verdict in {"OK", "WARN", "CRITICAL"}
