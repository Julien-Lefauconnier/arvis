# tests/cognition/conflict/test_conflict_modulation.py

from arvis.cognition.conflict.conflict_modulation import apply_conflict_to_risk


def test_no_conflict_no_change():
    assert apply_conflict_to_risk(0.5, 0.0) == 0.5


def test_conflict_increases_risk():
    r = apply_conflict_to_risk(0.5, 1.0, alpha=0.2)
    assert r > 0.5


def test_risk_is_bounded():
    r = apply_conflict_to_risk(0.9, 1.0, alpha=1.0)
    assert r <= 1.0


def test_zero_risk_stays_zero():
    assert apply_conflict_to_risk(0.0, 1.0) == 0.0