# arvis/cognition/conflict/conflict_evaluator.py

from collections.abc import Callable

from .conflict_policy_result import ConflictPolicyResult
from .conflict_signal import ConflictSignal


class ConflictEvaluator:
    """
    Applies conflict policies to arbitrary targets.

    - Pure
    - Stateless
    - Rule-driven
    """

    def __init__(
        self,
        rules: list[
            Callable[
                [list[ConflictPolicyResult], ConflictSignal],
                list[ConflictPolicyResult],
            ]
        ],
    ):
        self._rules = rules

    def apply(
        self,
        *,
        targets: list[str],
        conflicts: list[ConflictSignal],
    ) -> list[ConflictPolicyResult]:
        results = [ConflictPolicyResult(target_id=t) for t in targets]

        for conflict in conflicts:
            for rule in self._rules:
                try:
                    new_results = rule(results, conflict)
                    if new_results is not None:
                        results = new_results
                except Exception:
                    continue

        return results
