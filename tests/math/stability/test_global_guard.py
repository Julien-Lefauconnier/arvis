# tests/math/stability/test_global_guard.py

from arvis.math.stability.global_guard import GlobalStabilityGuard


def test_global_guard_stable():
    guard = GlobalStabilityGuard()
    assert guard.check([-0.1, -0.2, 0.05, -0.1]) is True


def test_global_guard_too_many_positive():
    guard = GlobalStabilityGuard(max_positive_ratio=0.5)
    assert guard.check([0.1, 0.2, 0.3, -0.1]) is False


def test_global_guard_cumulative_explosion():
    guard = GlobalStabilityGuard(max_cumulative_increase=0.5)
    assert guard.check([0.2, 0.3, 0.4]) is False
