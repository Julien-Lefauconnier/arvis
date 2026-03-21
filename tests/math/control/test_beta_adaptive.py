# tests/math/control/test_beta_adaptive.py


from arvis.math.control.beta_adaptive import (
    BetaAdaptiveController,
    BetaAdaptiveParams,
)
from arvis.math.stability.regime_estimator import RegimeSnapshot


# ============================================================
# Helper
# ============================================================

def make_regime(name):
    return RegimeSnapshot(regime=name, confidence=1.0, variance=0.0)


# ============================================================
# 1. NO REGIME (baseline)
# ============================================================

def test_no_regime():
    ctrl = BetaAdaptiveController()

    beta = ctrl.compute(
        regime=None,
        variance=0.0,
        drift=0.0,
    )

    assert beta == 1.0


# ============================================================
# 2. STABLE
# ============================================================

def test_stable_regime():
    ctrl = BetaAdaptiveController()

    beta = ctrl.compute(make_regime("stable"), 0.0, 0.0)

    assert beta == 1.5


# ============================================================
# 3. OSCILLATORY
# ============================================================

def test_oscillatory_regime():
    ctrl = BetaAdaptiveController()

    beta = ctrl.compute(make_regime("oscillatory"), 0.0, 0.0)

    assert beta == 2.0


# ============================================================
# 4. CRITICAL
# ============================================================

def test_critical_regime():
    ctrl = BetaAdaptiveController()

    beta = ctrl.compute(make_regime("critical"), 0.0, 0.0)

    assert beta == 3.0


# ============================================================
# 5. CHAOTIC
# ============================================================

def test_chaotic_regime():
    ctrl = BetaAdaptiveController()

    beta = ctrl.compute(make_regime("chaotic"), 0.0, 0.0)

    assert beta == 4.0


# ============================================================
# 6. TRANSITION
# ============================================================

def test_transition_regime():
    ctrl = BetaAdaptiveController()

    beta = ctrl.compute(make_regime("transition"), 0.0, 0.0)

    assert beta == 2.5


# ============================================================
# 7. VARIANCE + DRIFT EFFECT
# ============================================================

def test_variance_and_drift():
    ctrl = BetaAdaptiveController()

    beta = ctrl.compute(
        regime=None,
        variance=0.5,
        drift=0.5,
    )

    # 1.0 + (2*0.5) + (2*0.5) = 3.0
    assert beta == 3.0


# ============================================================
# 8. CLAMP MAX
# ============================================================

def test_clamp_max():
    ctrl = BetaAdaptiveController(
        BetaAdaptiveParams(beta_min=1.0, beta_max=5.0)
    )

    beta = ctrl.compute(
        regime=make_regime("chaotic"),  # +3
        variance=1.0,  # +2
        drift=1.0,     # +2
    )

    # theoretical = 1 + 3 + 2 + 2 = 8 → clamp to 5
    assert beta == 5.0


# ============================================================
# 9. CLAMP MIN (safety)
# ============================================================

def test_clamp_min():
    ctrl = BetaAdaptiveController(
        BetaAdaptiveParams(beta_min=2.0, beta_max=5.0)
    )

    beta = ctrl.compute(
        regime=None,
        variance=0.0,
        drift=0.0,
    )

    assert beta == 2.0


# ============================================================
# 10. UNKNOWN REGIME (robustness)
# ============================================================

def test_unknown_regime():
    ctrl = BetaAdaptiveController()

    beta = ctrl.compute(
        make_regime("unknown"),
        variance=0.0,
        drift=0.0,
    )

    # no boost applied
    assert beta == 1.0