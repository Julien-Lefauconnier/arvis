# tests/math/stability/test_hybrid_risk_observer.py

from arvis.math.stability.hybrid_risk_observer import HybridRiskObserver


def test_symbolic_energy_bounds():
    v = HybridRiskObserver.symbolic_energy(
        conflict_entropy=0.5,
        contradiction_density=0.4,
        gate_switch_rate=0.2,
        policy_disagreement_rate=0.1,
        symbolic_drift_score=0.3,
        edges_count=5,
        mean_edge_weight=0.6,
        max_edge_weight=0.8,
        spectral_proxy=0.4,
    )

    assert 0 <= v <= 1


def test_hybrid_fusion_basic():
    snap = HybridRiskObserver.fuse(
        v_numeric=0.4,
        v_symbolic=0.3,
    )

    assert 0 <= snap.collapse_risk <= 1
    assert snap.mode_hint in {"normal", "safe", "critical"}


def test_hybrid_delta_detection():
    snap = HybridRiskObserver.fuse(
        v_numeric=0.9,
        v_symbolic=0.8,
        prev_collapse_risk=0.3,
    )

    assert snap.delta > 0
    assert snap.collapse_risk >= 0.55
