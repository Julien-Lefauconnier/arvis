# tests/math/risk/test_confidence_sequence.py
"""Tests for the anytime-valid confidence-sequence risk bound.

Beyond basic algebra, the coverage tests SEARCH over many sequences -- i.i.d.
*and* adaptively adversarial -- evaluating the bound at every turn (optional
stopping). They confirm the bound covers the running conditional violation
propensity simultaneously for all ``n`` at the target rate, which is precisely
the guarantee the Hoeffding fixed-``n`` term cannot make.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from math import log, sqrt

import pytest

from arvis.math.risk.confidence_sequence import (
    ConfidenceSequenceParams,
    ConfidenceSequenceRiskBound,
)

Propensity = Callable[[list[int], random.Random], float]


def test_params_validation() -> None:
    with pytest.raises(ValueError):
        ConfidenceSequenceRiskBound(ConfidenceSequenceParams(delta=0.0))
    with pytest.raises(ValueError):
        ConfidenceSequenceRiskBound(ConfidenceSequenceParams(delta=1.0))
    with pytest.raises(ValueError):
        ConfidenceSequenceRiskBound(ConfidenceSequenceParams(horizon=0))


def test_ucb_brackets_phat_and_stays_in_unit_interval() -> None:
    rng = random.Random(0)
    cs = ConfidenceSequenceRiskBound()
    for _ in range(500):
        snap = cs.push(rng.random() < 0.3)
        assert 0.0 <= snap.p_hat <= 1.0
        assert 0.0 <= snap.p_ucb <= 1.0
        assert snap.p_ucb + 1e-12 >= snap.p_hat


def test_radius_is_monotone_decreasing() -> None:
    cs = ConfidenceSequenceRiskBound()
    radii = [cs.radius(n) for n in range(1, 2000)]
    assert all(b <= a + 1e-15 for a, b in zip(radii, radii[1:], strict=False))


def test_radius_matches_hoeffding_at_horizon() -> None:
    # At n = horizon the fixed-lambda radius equals the Hoeffding term.
    for horizon, delta in ((200, 0.01), (50, 0.05), (1000, 0.001)):
        cs = ConfidenceSequenceRiskBound(
            ConfidenceSequenceParams(horizon=horizon, delta=delta)
        )
        hoeffding = sqrt(log(1.0 / delta) / (2.0 * horizon))
        assert cs.radius(horizon) == pytest.approx(hoeffding, rel=1e-9)


def _anytime_miscoverage(
    propensity: Propensity, *, trials: int, n_max: int, delta: float, seed0: int
) -> float:
    """Fraction of trials where the CS upper bound under-covers the running
    average conditional propensity at SOME turn (optional stopping)."""
    misses = 0
    for t in range(trials):
        rng = random.Random(seed0 + t)
        cs = ConfidenceSequenceRiskBound(
            ConfidenceSequenceParams(horizon=200, delta=delta)
        )
        sum_p = 0.0
        bad = False
        history: list[int] = []
        for n in range(1, n_max + 1):
            p_s = propensity(history, rng)
            sum_p += p_s
            x = 1 if rng.random() < p_s else 0
            history.append(x)
            snap = cs.push(bool(x))
            if snap.p_ucb < sum_p / n:
                bad = True
        misses += int(bad)
    return misses / trials


def test_anytime_coverage_under_iid() -> None:
    def iid(_history: list[int], _rng: random.Random) -> float:
        return 0.2

    miss = _anytime_miscoverage(iid, trials=250, n_max=600, delta=0.05, seed0=10_000)
    assert miss <= 0.05


def test_anytime_coverage_under_adaptive_adversary() -> None:
    # Adversary raises its conditional propensity exactly when the running
    # empirical rate looks low, trying to slip above the bound undetected.
    def adversary(history: list[int], _rng: random.Random) -> float:
        if not history:
            return 0.5
        recent = sum(history[-20:]) / min(len(history), 20)
        return 0.85 if recent < 0.3 else 0.05

    miss = _anytime_miscoverage(
        adversary, trials=250, n_max=600, delta=0.05, seed0=20_000
    )
    assert miss <= 0.05


def _anytime_miscoverage_stitched(
    propensity: Propensity, *, trials: int, n_max: int, delta: float, seed0: int
) -> float:
    """As :func:`_anytime_miscoverage` but for the stitched, horizon-free
    boundary -- the coverage guarantee must survive the tighter radius."""
    misses = 0
    for t in range(trials):
        rng = random.Random(seed0 + t)
        cs = ConfidenceSequenceRiskBound(
            ConfidenceSequenceParams(horizon=200, delta=delta, boundary="stitched")
        )
        sum_p = 0.0
        bad = False
        history: list[int] = []
        for n in range(1, n_max + 1):
            p_s = propensity(history, rng)
            sum_p += p_s
            x = 1 if rng.random() < p_s else 0
            history.append(x)
            snap = cs.push(bool(x))
            if snap.p_ucb < sum_p / n:
                bad = True
        misses += int(bad)
    return misses / trials


def test_boundary_validation() -> None:
    with pytest.raises(ValueError):
        ConfidenceSequenceRiskBound(ConfidenceSequenceParams(boundary="nope"))
    with pytest.raises(ValueError):
        ConfidenceSequenceRiskBound(ConfidenceSequenceParams(stitch_eta=1.0))
    with pytest.raises(ValueError):
        ConfidenceSequenceRiskBound(ConfidenceSequenceParams(stitch_s=1.0))


def test_stitched_radius_is_monotone_decreasing() -> None:
    cs = ConfidenceSequenceRiskBound(ConfidenceSequenceParams(boundary="stitched"))
    radii = [cs.radius(n) for n in range(1, 2000)]
    assert all(b <= a + 1e-12 for a, b in zip(radii, radii[1:], strict=False))


def test_stitched_is_informative_where_fixed_lambda_saturates() -> None:
    # Motivating finding: at small n the fixed-lambda radius tuned at
    # horizon=200 is uninformative (near 1); the stitched radius is not.
    fixed = ConfidenceSequenceRiskBound(
        ConfidenceSequenceParams(horizon=200, delta=0.01, boundary="fixed_lambda")
    )
    stitched = ConfidenceSequenceRiskBound(
        ConfidenceSequenceParams(horizon=200, delta=0.01, boundary="stitched")
    )
    # fixed@200 saturates near 1 for small n; stitched is informative there.
    for n in (2, 4, 8, 12, 20):
        assert stitched.radius(n) < fixed.radius(n)
    assert stitched.radius(12) < 0.7  # descending and usable, not pinned at 1


def test_stitched_tightness_within_loglog_factor() -> None:
    # Stitched radius stays within a bounded multiple of the (non-anytime)
    # pointwise Hoeffding optimum -- the log-log price, not a blow-up.
    delta = 0.01
    cs = ConfidenceSequenceRiskBound(
        ConfidenceSequenceParams(delta=delta, boundary="stitched")
    )
    for n in (12, 50, 150, 500, 1500):
        pointwise = sqrt(log(1.0 / delta) / (2.0 * n))
        assert cs.radius(n) <= 1.7 * pointwise


def test_stitched_truncation_matches_full_sweep() -> None:
    # Truncating the epoch sweep only raises the min (validity); with the
    # default pad it must already equal a far wider sweep (no tightness lost).
    narrow = ConfidenceSequenceRiskBound(
        ConfidenceSequenceParams(boundary="stitched", stitch_k_pad=3)
    )
    wide = ConfidenceSequenceRiskBound(
        ConfidenceSequenceParams(boundary="stitched", stitch_k_pad=40)
    )
    for n in (1, 3, 12, 60, 250, 900, 5000):
        assert narrow.radius(n) == pytest.approx(wide.radius(n), rel=1e-12)
        assert narrow.radius(n) + 1e-15 >= wide.radius(n)


def test_stitched_ucb_brackets_phat_and_in_unit_interval() -> None:
    rng = random.Random(7)
    cs = ConfidenceSequenceRiskBound(ConfidenceSequenceParams(boundary="stitched"))
    for _ in range(500):
        snap = cs.push(rng.random() < 0.3)
        assert 0.0 <= snap.p_hat <= 1.0
        assert 0.0 <= snap.p_ucb <= 1.0
        assert snap.p_ucb + 1e-12 >= snap.p_hat


def test_stitched_anytime_coverage_under_iid() -> None:
    def iid(_history: list[int], _rng: random.Random) -> float:
        return 0.2

    miss = _anytime_miscoverage_stitched(
        iid, trials=250, n_max=600, delta=0.05, seed0=30_000
    )
    assert miss <= 0.05


def test_stitched_anytime_coverage_under_adaptive_adversary() -> None:
    def adversary(history: list[int], _rng: random.Random) -> float:
        if not history:
            return 0.5
        recent = sum(history[-20:]) / min(len(history), 20)
        return 0.85 if recent < 0.3 else 0.05

    miss = _anytime_miscoverage_stitched(
        adversary, trials=250, n_max=600, delta=0.05, seed0=40_000
    )
    assert miss <= 0.05
