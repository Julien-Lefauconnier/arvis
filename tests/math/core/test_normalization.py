# tests/math/core/test_normalization.py

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