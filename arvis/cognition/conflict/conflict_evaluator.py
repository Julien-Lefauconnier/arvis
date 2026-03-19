# arvis/cognition/conflict/conflict_evaluator.py

from typing import Callable, List

from .conflict_signal import ConflictSignal
from .conflict_policy_result import ConflictPolicyResult


class ConflictEvaluator:
    """
    Applies conflict policies to arbitrary targets.

    - Pure
    - Stateless
    - Rule-driven
    """

    def __init__(
        self,
        rules: List[
            Callable[
                [List[ConflictPolicyResult], ConflictSignal],
                List[ConflictPolicyResult],
            ]
        ],
    ):
        self._rules = rules

    def apply(
        self,
        *,
        targets: List[str],
        conflicts: List[ConflictSignal],
    ) -> List[ConflictPolicyResult]:

        results = [
            ConflictPolicyResult(target_id=t)
            for t in targets
        ]

        for conflict in conflicts:
            for rule in self._rules:
                try:
                    new_results = rule(results, conflict)
                    if new_results is not None:
                        results = new_results
                except Exception:
                    continue

        return results