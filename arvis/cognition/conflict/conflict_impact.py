# arvis/cognition/conflict/conflict_impact.py

from typing import List

from .conflict_policy_result import ConflictPolicyResult


def compute_conflict_pressure(conflicts: List[ConflictPolicyResult]) -> float:
    """
    Computes a normalized conflict pressure signal.

    Pure function.
    No side effects.
    """

    if not conflicts:
        return 0.0

    # v1: any conflict → full pressure
    return 1.0