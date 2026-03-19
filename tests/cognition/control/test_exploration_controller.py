# tests/cognition/control/test_exploration_controller.py

from arvis.cognition.control.exploration_controller import ExplorationController


def test_default_behavior():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime=None,
        collapse_risk=0.0,
        drift_score=0.0,
        stable=True,
    )

    assert result.exploration_factor == 1.0
    assert result.confirmation_bias == 1.0
    assert result.change_budget_scale == 1.0
    assert "base" in result.rationale


# -----------------------------
# Regimes
# -----------------------------

def test_stable_regime():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime="stable",
        collapse_risk=0.0,
        drift_score=0.0,
        stable=True,
    )

    assert result.exploration_factor > 1.0
    assert "regime=stable" in result.rationale


def test_critical_regime():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime="critical",
        collapse_risk=0.0,
        drift_score=0.0,
        stable=True,
    )

    assert result.exploration_factor < 1.0
    assert result.confirmation_bias > 1.0
    assert "regime=critical" in result.rationale


def test_chaotic_regime():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime="chaotic",
        collapse_risk=0.0,
        drift_score=0.0,
        stable=True,
    )

    assert result.exploration_factor <= 1.0
    assert result.abstain_bias > 1.0
    assert "regime=chaotic" in result.rationale


# -----------------------------
# Risk thresholds
# -----------------------------

def test_high_risk():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime=None,
        collapse_risk=0.9,
        drift_score=0.0,
        stable=True,
    )

    assert result.confirmation_bias > 1.0
    assert "collapse>=0.8" in result.rationale


def test_medium_risk():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime=None,
        collapse_risk=0.6,
        drift_score=0.0,
        stable=True,
    )

    assert result.exploration_factor < 1.0
    assert "collapse>=0.5" in result.rationale


# -----------------------------
# Drift
# -----------------------------

def test_high_drift():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime=None,
        collapse_risk=0.0,
        drift_score=0.8,
        stable=True,
    )

    assert result.confirmation_bias > 1.0
    assert "drift>=0.7" in result.rationale


# -----------------------------
# Stability flag
# -----------------------------

def test_unstable_flag():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime=None,
        collapse_risk=0.0,
        drift_score=0.0,
        stable=False,
    )

    assert result.exploration_factor < 1.0
    assert "unstable" in result.rationale


# -----------------------------
# Clamp behavior
# -----------------------------

def test_clamping_bounds():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime="chaotic",
        collapse_risk=1.0,
        drift_score=1.0,
        stable=False,
    )

    assert 0.3 <= result.exploration_factor <= 1.5
    assert 0.7 <= result.confirmation_bias <= 2.0
    assert 0.8 <= result.abstain_bias <= 2.0
    assert 0.5 <= result.change_budget_scale <= 1.3


# -----------------------------
# Robustness (None inputs)
# -----------------------------

def test_none_inputs():
    ctrl = ExplorationController()

    result = ctrl.compute(
        regime=None,
        collapse_risk=None,
        drift_score=None,
        stable=None,
    )

    assert result is not None