# arvis/cognition/conflict/default_rules.py

from typing import List, Callable

from .conflict_signal import ConflictSignal
from .conflict_policy_result import ConflictPolicyResult


def noop_rule(
    results: List[ConflictPolicyResult],
    conflict: ConflictSignal,
) -> List[ConflictPolicyResult]:
    """
    Default no-op rule (safe baseline).
    """
    return results


def default_conflict_rules() -> List[
    Callable[[List[ConflictPolicyResult], ConflictSignal], List[ConflictPolicyResult]]
]:
    return [noop_rule]