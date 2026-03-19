# tests/cognition/conflict/test_conflict_confirmation.py

from arvis.cognition.conflict.conflict_confirmation import requires_conflict_confirmation


def test_no_conflict_no_confirmation():
    assert not requires_conflict_confirmation(0.0)


def test_low_conflict_no_confirmation():
    assert not requires_conflict_confirmation(0.3)


def test_high_conflict_triggers_confirmation():
    assert requires_conflict_confirmation(0.7)