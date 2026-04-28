# tests/contracts/test_no_instability_spike.py

from arvis.math.signals.coercion import to_risk


def test_no_large_risk_jump():
    r1 = to_risk(0.2)
    r2 = to_risk(0.9)

    assert float(r2) - float(r1) <= 1.0
