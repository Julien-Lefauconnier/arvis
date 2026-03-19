# tests/contracts/test_drift_bounds.py

from arvis.math.signals.coercion import to_drift


def test_drift_is_bounded():
    for val in [-10, 0, 0.5, 2, 100]:
        d = to_drift(val)
        assert 0.0 <= float(d) <= 1.0