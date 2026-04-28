# tests/math/adaptive/test_adaptive_kappa_eff.py

import math

import pytest

from arvis.math.adaptive.adaptive_kappa_eff import (
    AdaptiveKappaConfig,
    AdaptiveKappaEffEstimator,
)


def test_unavailable_when_previous_energy_too_small():
    est = AdaptiveKappaEffEstimator()

    snap = est.update(W_prev=0.0, W_next=1.0)

    assert snap.is_available is False
    assert snap.regime == "unavailable"
    assert snap.kappa_raw is None


def test_positive_decay_gives_positive_kappa():
    est = AdaptiveKappaEffEstimator()

    snap = est.update(W_prev=10.0, W_next=8.0)

    assert snap.is_available is True
    assert snap.kappa_raw == pytest.approx(0.2)
    assert snap.kappa_clipped == pytest.approx(0.2)
    assert snap.kappa_smoothed == pytest.approx(0.2)
    assert snap.regime == "stable"


def test_growth_gives_unstable_regime():
    est = AdaptiveKappaEffEstimator()

    snap = est.update(W_prev=10.0, W_next=12.0)

    assert snap.is_available is True
    assert snap.kappa_raw == pytest.approx(-0.2)
    assert snap.kappa_clipped == pytest.approx(0.0)
    assert snap.kappa_smoothed == pytest.approx(0.0)
    assert snap.regime == "unstable"


def test_smoothing_behaves_as_expected():
    est = AdaptiveKappaEffEstimator(AdaptiveKappaConfig(smoothing=0.5))

    snap1 = est.update(W_prev=10.0, W_next=8.0)  # raw = 0.2
    snap2 = est.update(W_prev=8.0, W_next=7.2)  # raw = 0.1

    assert snap1.kappa_smoothed == pytest.approx(0.2)
    assert snap2.kappa_smoothed == pytest.approx(0.15)


def test_switching_margin_is_defined_after_update():
    est = AdaptiveKappaEffEstimator()
    est.update(W_prev=10.0, W_next=8.0)

    margin = est.adaptive_switching_margin(J=1.2, tau_d=10.0)

    assert margin is not None
    assert not math.isnan(margin)
    assert not math.isinf(margin)


def test_switching_margin_requires_positive_parameters():
    est = AdaptiveKappaEffEstimator()
    est.update(W_prev=10.0, W_next=8.0)

    with pytest.raises(ValueError):
        est.adaptive_switching_margin(J=0.0, tau_d=10.0)

    with pytest.raises(ValueError):
        est.adaptive_switching_margin(J=1.2, tau_d=0.0)
