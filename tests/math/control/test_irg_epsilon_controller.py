# tests/math/control/test_irg_epsilon_controller.py

from arvis.math.control.irg_epsilon_controller import IRGEpsilonController, IRGRegime
from arvis.math.control.eps_adaptive import EpsAdaptiveParams, CognitiveMode
from arvis.math.signals import RiskSignal


def make_controller():
    return IRGEpsilonController(adaptive_params=EpsAdaptiveParams(enabled=True))


def test_infer_regime_collapse_from_critical_signal():
    ctl = make_controller()
    regime = ctl.infer_regime(
        collapse_risk=RiskSignal(0.9),
        latent_volatility=0.1,
    )
    assert regime == IRGRegime.COLLAPSE


def test_infer_regime_unstable_from_risk_zone():
    ctl = make_controller()
    regime = ctl.infer_regime(
        collapse_risk=RiskSignal(0.7),
        latent_volatility=0.1,
    )
    assert regime == IRGRegime.UNSTABLE


def test_infer_regime_transition_from_risk_zone():
    ctl = make_controller()
    regime = ctl.infer_regime(
        collapse_risk=RiskSignal(0.4),
        latent_volatility=0.1,
    )
    assert regime == IRGRegime.TRANSITION


def test_infer_regime_stable_when_low_risk_and_low_volatility():
    ctl = make_controller()
    regime = ctl.infer_regime(
        collapse_risk=RiskSignal(0.1),
        latent_volatility=0.1,
    )
    assert regime == IRGRegime.STABLE


def test_compute_accepts_signal_inputs():
    ctl = make_controller()
    eps = ctl.compute(
        uncertainty=0.2,
        budget_used=0.3,
        delta_v=0.1,
        collapse_risk=RiskSignal(0.4),
        latent_volatility=0.2,
        mode=CognitiveMode.NORMAL,
    )
    assert eps >= 0.0
