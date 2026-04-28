# tests/cognition/conflict/test_conflict_impact.py

from arvis.cognition.conflict.conflict_impact import compute_conflict_pressure
from arvis.cognition.conflict.conflict_policy_result import ConflictPolicyResult


def test_conflict_pressure_empty():
    assert compute_conflict_pressure([]) == 0.0


def test_conflict_pressure_partial():
    conflicts = [
        ConflictPolicyResult(target_id="a"),
        ConflictPolicyResult(target_id="b"),
    ]
    assert compute_conflict_pressure(conflicts) == 1.0


def test_conflict_pressure_full():
    conflicts = [
        ConflictPolicyResult(target_id="a"),
        ConflictPolicyResult(target_id="b"),
    ]
    assert compute_conflict_pressure(conflicts) == 1.0
