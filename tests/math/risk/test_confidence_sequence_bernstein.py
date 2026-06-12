# tests/math/risk/test_confidence_sequence_bernstein.py
"""Variance-adaptive (empirical-Bernstein) confidence-sequence boundary.

On a clean session (no violations => predictable variance 0) the radius decays
like the range term ~ c*ell/n, far tighter than the variance-agnostic stitched
~1/sqrt(n). At high empirical variance the two converge.
"""

from __future__ import annotations

import pytest

from arvis.math.risk.confidence_sequence import (
    ConfidenceSequenceParams,
    ConfidenceSequenceRiskBound,
)


def _bound(boundary: str) -> ConfidenceSequenceRiskBound:
    return ConfidenceSequenceRiskBound(ConfidenceSequenceParams(boundary=boundary))


def test_clean_session_radius_much_tighter_than_stitched() -> None:
    bern = _bound("bernstein")
    stit = _bound("stitched")
    for n in (30, 50, 100):
        assert bern.radius(n, var_pred=0.0) < stit.radius(n)


def test_radius_grows_with_predictable_variance() -> None:
    bern = _bound("bernstein")
    assert bern.radius(100, var_pred=10.0) > bern.radius(100, var_pred=0.0)


def test_clean_session_reaches_ok_far_sooner() -> None:
    bern = _bound("bernstein")
    stit = _bound("stitched")
    n_ok_bern = next(n for n in range(1, 5000) if bern.radius(n, 0.0) < 0.10)
    n_ok_stit = next(n for n in range(1, 5000) if stit.radius(n) < 0.10)
    assert n_ok_bern < n_ok_stit / 3  # at least 3x faster


def test_evaluate_uses_var_pred() -> None:
    bound = _bound("bernstein")
    snap = bound.evaluate(50, 0, var_pred=0.0)
    assert snap.p_ucb < 0.20  # tight on clean session


def test_push_accumulates_predictable_variance() -> None:
    bound = _bound("bernstein")
    snap = None
    # alternating history => p_hat ~ 0.5 => predictable variance accumulates;
    # 40 turns keeps the radius below the p_ucb=1.0 cap so the effect is visible.
    for i in range(40):
        snap = bound.push(i % 2 == 0)
    assert snap is not None
    # same (n=40, violations=20) but ignoring variance: accumulated var widens it
    flat = _bound("bernstein").evaluate(40, 20, var_pred=0.0)
    assert snap.p_ucb > flat.p_ucb


def test_rejects_unknown_boundary() -> None:
    with pytest.raises(ValueError):
        ConfidenceSequenceRiskBound(ConfidenceSequenceParams(boundary="nope"))
