# arvis/cognition/governance/governance_evaluator.py

from typing import Optional

from .governance_decision import GovernanceDecision
from .governance_suggestion import GovernanceSuggestion


class GovernanceEvaluator:
    """
    Stateless governance evaluator.

    Matches decisions to suggestions.
    """

    def evaluate(
        self,
        *,
        suggestion: GovernanceSuggestion,
        decision: Optional[GovernanceDecision],
    ) -> Optional[GovernanceDecision]:
        if decision is None:
            return None

        if decision.suggestion_id != suggestion.suggestion_id:
            return None

        return decision
