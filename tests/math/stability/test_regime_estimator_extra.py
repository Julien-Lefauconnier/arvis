# tests/math/stability/test_regime_estimator_extra.py

import pytest

from arvis.math.stability.regime_estimator import CognitiveRegimeEstimator

# ============================================================
# 1. INIT VALIDATION
# ============================================================


def test_invalid_window():
    with pytest.raises(ValueError):
        CognitiveRegimeEstimator(window=0)


def test_invalid_min_samples():
    with pytest.raises(ValueError):
        CognitiveRegimeEstimator(min_samples=0)


# ============================================================
# 2. NOT ENOUGH SAMPLES
# ============================================================


def test_not_enough_samples():
    est = CognitiveRegimeEstimator(min_samples=5)

    for _ in range(4):
        assert est.push(-0.1) is None


# ============================================================
# 3. STABLE REGIME
# contraction > 0.9 AND var < 0.01
# ============================================================


def test_stable_regime():
    est = CognitiveRegimeEstimator(min_samples=5)

    for _ in range(5):
        snap = est.push(-0.001)

    assert snap.regime == "stable"
    assert snap.confidence == 0.9


# ============================================================
# 4. OSCILLATORY REGIME
# contraction > 0.7 AND var < 0.1
# ============================================================


def test_oscillatory_regime():
    est = CognitiveRegimeEstimator(min_samples=5)

    values = [-0.1, -0.2, -0.1, -0.05, 0.01]

    for v in values:
        snap = est.push(v)

    assert snap.regime == "oscillatory"
    assert snap.confidence == 0.7


# ============================================================
# 5. CRITICAL REGIME
# contraction > 0.5
# ============================================================


def test_critical_regime():
    est = CognitiveRegimeEstimator(min_samples=5)

    values = [-0.1, -0.2, -0.1, 0.2, 0.3]

    for v in values:
        snap = est.push(v)

    assert snap.regime == "critical"
    assert snap.confidence == 0.6


# ============================================================
# 6. CHAOTIC REGIME
# var > 0.2
# ============================================================


def test_chaotic_regime():
    est = CognitiveRegimeEstimator(min_samples=5)

    values = [-1, 1, -1, 1, 0]

    for v in values:
        snap = est.push(v)

    assert snap.regime == "chaotic"
    assert snap.confidence == 0.8


# ============================================================
# 7. TRANSITION REGIME
# fallback case
# ============================================================


def test_transition_regime():
    est = CognitiveRegimeEstimator(min_samples=5)

    values = [-0.1, 0.1, -0.1, 0.1, 0.0]

    for v in values:
        snap = est.push(v)

    assert snap.regime == "transition"
    assert snap.confidence == 0.5


# ============================================================
# 8. TYPE SAFETY (float coercion)
# ============================================================


def test_push_casts_to_float():
    est = CognitiveRegimeEstimator(min_samples=3)

    est.push(1)
    est.push(2)
    snap = est.push(3)

    assert snap is not None
    assert isinstance(snap.variance, float)
