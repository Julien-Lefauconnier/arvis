# tests/contracts/test_coercion_safety.py

from arvis.math.signals.coercion import to_float


def test_to_float_never_crashes():
    class Bad:
        pass

    assert to_float(None) == 0.0
    assert to_float("invalid") == 0.0
    assert to_float(Bad()) == 0.0
