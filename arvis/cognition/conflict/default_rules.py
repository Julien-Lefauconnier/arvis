# arvis/cognition/conflict/default_rules.py

from collections.abc import Callable

from .conflict_policy_result import ConflictPolicyResult
from .conflict_signal import ConflictSignal


def noop_rule(
    results: list[ConflictPolicyResult],
    conflict: ConflictSignal,
) -> list[ConflictPolicyResult]:
    """
    Default no-op rule (safe baseline).
    """
    return results


def default_conflict_rules() -> list[
    Callable[[list[ConflictPolicyResult], ConflictSignal], list[ConflictPolicyResult]]
]:
    return [noop_rule]
