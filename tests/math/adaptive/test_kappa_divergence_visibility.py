# tests/math/adaptive/test_kappa_divergence_visibility.py
"""A divergence must never be classified "stable" (audit G5, M4).

The previous estimator clipped the raw factor at 0.0 BEFORE smoothing:
after six healthy steps (smoothed 0.5), an energy blow-up from 1.0 to
100.0 produced kappa_raw = -99, clipped to 0.0, smoothed to 0.4, regime
"stable". The clipping destroyed the divergence's magnitude before
anything could react.

Now: the reporting floor is -1.0 (a doubling or worse stays visible to
the smoother), and consecutive raw divergences are counted on the RAW
value; one divergence caps the regime at "marginal", a streak forces
"unstable" regardless of the smoothed history.
"""

from __future__ import annotations

from arvis.math.adaptive.adaptive_kappa_eff import AdaptiveKappaEffEstimator


def _healthy(estimator: AdaptiveKappaEffEstimator, steps: int = 6) -> None:
    for _ in range(steps):
        estimator.update(1.0, 0.5)


def test_single_massive_divergence_is_never_stable() -> None:
    est = AdaptiveKappaEffEstimator()
    _healthy(est)
    snap = est.update(1.0, 100.0)
    assert snap.kappa_raw is not None and snap.kappa_raw < -1.0
    assert snap.kappa_clipped == -1.0, "the floor must keep the divergence visible"
    assert snap.regime != "stable", (
        "a step where the energy grew a hundredfold cannot be 'stable' "
        f"(got {snap.regime}, smoothed={snap.kappa_smoothed})"
    )
    assert snap.divergence_streak == 1


def test_divergence_streak_forces_unstable() -> None:
    est = AdaptiveKappaEffEstimator()
    _healthy(est)
    for _ in range(est.config.divergence_streak_limit):
        snap = est.update(1.0, 2.0)
    assert snap.regime == "unstable", (
        "three consecutive divergences must be unstable whatever the "
        f"smoothed history says (smoothed={snap.kappa_smoothed})"
    )


def test_recovery_resets_the_streak() -> None:
    est = AdaptiveKappaEffEstimator()
    _healthy(est)
    est.update(1.0, 2.0)
    snap = est.update(1.0, 0.5)
    assert snap.divergence_streak == 0


def test_healthy_history_stays_stable() -> None:
    est = AdaptiveKappaEffEstimator()
    _healthy(est)
    snap = est.update(1.0, 0.5)
    assert snap.regime == "stable"
    assert snap.divergence_streak == 0
