# arvis/cognition/coherence/stability_constraint.py

from dataclasses import dataclass
from typing import Optional

from arvis.cognition.coherence.change_budget import ChangeBudget


@dataclass(frozen=True)
class StabilityConstraintResult:
    """
    Declarative evaluation result.

    - non prescriptive
    - does not enforce
    - suitable for audit / governance / UI
    """
    stable: bool
    violation: int
    rationale: str


class StabilityConstraint:
    """
    Stability constraint over a ChangeBudget.

    ZKCS-safe:
    - no content access
    - uses only declarative counters
    """

    @staticmethod
    def evaluate(budget: ChangeBudget) -> StabilityConstraintResult:
        """
        Stable iff current_changes <= max_changes.
        """
        violation = max(0, budget.current_changes - budget.max_changes)
        stable = violation == 0

        if stable:
            rationale = "Within change budget"
        else:
            rationale = "Change budget exceeded, potential instability detected"

        return StabilityConstraintResult(
            stable=stable,
            violation=violation,
            rationale=rationale,
        )

    @staticmethod
    def should_warn(budget: ChangeBudget) -> bool:
        """
        Convenience helper for policies.
        """
        return budget.current_changes > budget.max_changes

    @staticmethod
    def should_abstain(
        budget: ChangeBudget,
        *,
        hard_threshold: Optional[int] = None,
    ) -> bool:
        """
        Optional helper if you later couple stability to the gate.

        hard_threshold:
            If set, abstain when violation >= hard_threshold.
        """
        if hard_threshold is None:
            return False
        return (budget.current_changes - budget.max_changes) >= hard_threshold