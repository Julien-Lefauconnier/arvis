# tests/contracts/test_lyapunov_sanity.py

from arvis.math.lyapunov.lyapunov import V


def test_lyapunov_non_negative():
    assert V(0.0) >= 0.0
    assert V(1.0) >= 0.0