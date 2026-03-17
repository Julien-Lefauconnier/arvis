# tests/math/stability/test_regime_estimator.py

from arvis.math.stability.regime_estimator import CognitiveRegimeEstimator


def test_regime_estimator_initial_state():
    est = CognitiveRegimeEstimator(window=20, min_samples=5)

    for _ in range(4):
        assert est.push(-0.01) is None


def test_regime_estimator_stable_detection():
    est = CognitiveRegimeEstimator(window=20, min_samples=5)

    snap = None
    for _ in range(10):
        snap = est.push(-0.01)

    assert snap is not None
    assert snap.regime == "stable"
    assert snap.confidence >= 0.8
    assert snap.variance < 0.01


def test_regime_estimator_chaotic_detection():
    est = CognitiveRegimeEstimator(window=20, min_samples=5)

    values = [0.5, -0.4, 0.6, -0.7, 0.8, -0.5, 0.9]

    snap = None
    for v in values:
        snap = est.push(v)

    assert snap is not None
    assert snap.regime in {"chaotic", "critical", "transition"}