# tests/math/signals/test_base_signal.py

import pytest

from arvis.math.signals.base import BaseSignal


# ============================================================
# Helper
# ============================================================


class DummyFloat:
    def __float__(self):
        return 0.5


class BrokenFloat:
    def __float__(self):
        raise ValueError


# ============================================================
# 1. BASIC API
# ============================================================


def test_level_and_float():
    s = BaseSignal(0.3)

    assert s.level() == 0.3
    assert float(s) == 0.3


# ============================================================
# 2. COMPARATORS WITH FLOAT
# ============================================================


def test_comparators_float():
    s = BaseSignal(0.5)

    assert s < 0.6
    assert s <= 0.5
    assert s > 0.4
    assert s >= 0.5


# ============================================================
# 3. COMPARATORS WITH OBJECT
# ============================================================


def test_comparators_object():
    s = BaseSignal(0.5)

    other = DummyFloat()

    assert s == other
    assert not (s < other)
    assert not (s > other)


# ============================================================
# 4. EQ WITH INVALID OBJECT (exception path)
# ============================================================


def test_eq_exception_path():
    s = BaseSignal(0.5)

    other = BrokenFloat()

    assert (s == other) is False


# ============================================================
# 5. EQ WITH NON-FLOATABLE OBJECT
# ============================================================


def test_eq_non_floatable():
    s = BaseSignal(0.5)

    assert (s == "abc") is False


# ============================================================
# 6. IS_ZERO
# ============================================================


def test_is_zero():
    assert BaseSignal(0.0).is_zero() is True
    assert BaseSignal(0.1).is_zero() is False


# ============================================================
# 7. IS_MAX
# ============================================================


def test_is_max():
    assert BaseSignal(1.0).is_max() is True
    assert BaseSignal(0.9).is_max() is False


# ============================================================
# 8. CROSS COMPARISON BETWEEN SIGNALS
# ============================================================


def test_signal_to_signal_comparison():
    s1 = BaseSignal(0.3)
    s2 = BaseSignal(0.7)

    assert s1 < s2
    assert s2 > s1
    assert s1 != s2


# ============================================================
# 9. IMMUTABILITY (important contract)
# ============================================================


def test_immutable():
    s = BaseSignal(0.5)

    with pytest.raises(Exception):
        s.value = 0.2
