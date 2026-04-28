# tests/math/core/test_normalization.py

import pytest

from arvis.math.core.normalization import clamp, clamp01


def test_clamp_inside_range():
    assert clamp(0.5, 0, 1) == 0.5


def test_clamp_below_range():
    assert clamp(-1, 0, 1) == 0


def test_clamp_above_range():
    assert clamp(2, 0, 1) == 1


def test_clamp01():
    assert clamp01(0.2) == 0.2
    assert clamp01(-1) == 0
    assert clamp01(2) == 1


def test_clamp_edge_cases():
    from arvis.math.core.normalization import clamp

    assert clamp(5, 0, 1) == 1
    assert clamp(-1, 0, 1) == 0
    assert clamp(0.5, 0, 1) == 0.5
    assert clamp(float("inf"), 0, 1) == 0


def test_safe_div():
    from arvis.math.core.normalization import safe_div

    assert safe_div(1, 2) == 0.5
    assert safe_div(1, 0) == 0.0
    assert safe_div(float("inf"), 1) == 0.0


def test_sigmoid_and_tanh():
    from arvis.math.core.normalization import sigmoid01, tanh01

    assert 0.0 <= sigmoid01(0) <= 1.0
    assert 0.0 <= tanh01(0) <= 1.0

    assert sigmoid01(float("inf")) == 0.0
    assert tanh01(float("nan")) == 0.0


def test_affine_invalid_bounds():
    from arvis.math.core.normalization import affine01

    assert affine01(5, x_min=1, x_max=1) == 0.0


def test_normalize_weights_edge():
    from arvis.math.core.normalization import normalize_weights

    assert normalize_weights([]) == []
    assert normalize_weights([0, 0]) == [0.5, 0.5]
    assert sum(normalize_weights([1, 1])) == 1.0


def test_weighted_sum_mismatch():
    from arvis.math.core.normalization import weighted_sum01

    with pytest.raises(ValueError):
        weighted_sum01([0.1], [0.1, 0.2])


def test_budget_ratio_edge():
    from arvis.math.core.normalization import budget_ratio01

    assert budget_ratio01(1, 0) == 1.0
    assert budget_ratio01(float("nan"), 1) == 1.0
