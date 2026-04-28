# tests/math/adaptive/test_adaptive_kappa_eff_trajectory.py

from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator


def test_adaptive_kappa_tracks_stable_decay_trajectory():
    est = AdaptiveKappaEffEstimator()

    W_values = [10.0, 9.0, 8.1, 7.29, 6.561]
    snaps = []

    for prev, nxt in zip(W_values[:-1], W_values[1:], strict=True):
        snaps.append(est.update(W_prev=prev, W_next=nxt))

    assert all(s.is_available for s in snaps)
    assert snaps[-1].kappa_smoothed is not None
    assert snaps[-1].kappa_smoothed > 0.05
    assert snaps[-1].regime == "stable"


def test_adaptive_kappa_detects_unstable_growth_trajectory():
    est = AdaptiveKappaEffEstimator()

    W_values = [10.0, 11.0, 12.1, 13.31]
    snaps = []

    for prev, nxt in zip(W_values[:-1], W_values[1:], strict=True):
        snaps.append(est.update(W_prev=prev, W_next=nxt))

    assert all(s.is_available for s in snaps)
    assert snaps[-1].kappa_smoothed is not None
    assert snaps[-1].kappa_smoothed <= 0.0
    assert snaps[-1].regime == "unstable"
