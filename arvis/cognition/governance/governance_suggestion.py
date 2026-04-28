# arvis/cognition/governance/governance_suggestion.py

from dataclasses import dataclass


@dataclass(frozen=True)
class GovernanceSuggestion:
    """
    Declarative governance suggestion.
    """

    suggestion_id: str
    source_policy: str
    dimension: str
    suggestion_type: str
    rationale: str
