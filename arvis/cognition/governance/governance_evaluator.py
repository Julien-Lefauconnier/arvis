# arvis/cognition/governance/governance_evaluator.py


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
        decision: GovernanceDecision | None,
    ) -> GovernanceDecision | None:
        if decision is None:
            return None

        if decision.suggestion_id != suggestion.suggestion_id:
            return None

        return decision
