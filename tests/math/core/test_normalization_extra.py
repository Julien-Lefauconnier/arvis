# tests/math/core/test_normalization_extra.py

import math
import pytest

from arvis.math.core.normalization import (
    affine01,
    weighted_sum01,
    budget_ratio01,
    NormalizedSignals,
)


def test_affine01_non_finite():
    assert affine01(math.inf, x_min=0, x_max=1) == 0.0
    assert affine01(1, x_min=math.nan, x_max=1) == 0.0

def test_affine01_degenerate_interval():
    assert affine01(0.5, x_min=1.0, x_max=1.0) == 0.0

def test_weighted_sum_length_mismatch():
    with pytest.raises(ValueError):
        weighted_sum01([0.1, 0.2], [1.0])


def test_budget_ratio_non_finite():
    import math

    assert budget_ratio01(math.nan, 1.0) == 1.0
    assert budget_ratio01(1.0, math.inf) == 1.0

def test_budget_ratio_zero_max():
    assert budget_ratio01(1.0, 0.0) == 1.0

def test_normalized_signals_clamping():
    s = NormalizedSignals(
        risk=2.0,
        drift=-1.0,
        uncertainty=0.5,
        budget_used=10.0,
    )

    assert s.risk == 1.0
    assert s.drift == 0.0
    assert s.uncertainty == 0.5
    assert s.budget_used == 1.0

