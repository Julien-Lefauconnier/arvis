# tests/contracts/test_risk_stability.py

from arvis.math.signals.coercion import to_risk


def test_risk_never_explodes():
    r1 = to_risk(0.2)
    r2 = to_risk(0.25)
    r3 = to_risk(0.3)

    assert r1 <= r2 <= r3
