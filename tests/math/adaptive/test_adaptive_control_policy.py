# tests/math/adaptive/test_adaptive_control_policy.py

from arvis.math.adaptive.adaptive_control_policy import AdaptiveControlPolicy


def test_unstable_regime_is_conservative():
    policy = AdaptiveControlPolicy()

    out = policy.compute(
        kappa_eff=0.0,
        margin=0.1,
        regime="unstable",
    )

    assert out.exploration_scale < 0.3
    assert out.conservatism_scale > 1.5
    assert out.risk_tolerance_scale < 0.5


def test_stable_regime_allows_exploration():
    policy = AdaptiveControlPolicy()

    out = policy.compute(
        kappa_eff=0.5,
        margin=-0.1,
        regime="stable",
    )

    assert out.exploration_scale > 0.5
    assert out.conservatism_scale < 1.5
    assert out.risk_tolerance_scale > 0.5


def test_higher_kappa_means_more_exploration():
    policy = AdaptiveControlPolicy()

    out_low = policy.compute(
        kappa_eff=0.2,
        margin=-0.1,
        regime="stable",
    )

    out_high = policy.compute(
        kappa_eff=0.8,
        margin=-0.1,
        regime="stable",
    )

    assert out_high.exploration_scale > out_low.exploration_scale
    assert out_high.conservatism_scale < out_low.conservatism_scale


def test_fallback_behavior():
    policy = AdaptiveControlPolicy()

    out = policy.compute(
        kappa_eff=None,
        margin=None,
        regime=None,
    )

    assert out.regime == "fallback"
