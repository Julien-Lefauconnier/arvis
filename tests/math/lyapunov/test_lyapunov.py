# tests/math/lyapunov/test_lyapunov.py

from arvis.math.lyapunov.lyapunov import (
    LyapunovState,
    lyapunov_value,
)


def test_lyapunov_value_non_negative():

    s = LyapunovState(
        budget_used=0.2,
        risk=0.3,
        uncertainty=0.1,
        governance=0.1,
    )

    value = lyapunov_value(s)

    assert value >= 0