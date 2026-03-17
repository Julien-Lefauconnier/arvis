# arvis/cognition/governance/governance_decision.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GovernanceDecisionType(str, Enum):
    ACCEPTED = "accepted"
    REFUSED = "refused"
    REVOKED = "revoked"


@dataclass(frozen=True)
class GovernanceDecision:
    """
    Declarative governance decision.
    """

    suggestion_id: str
    decision: GovernanceDecisionType
    decided_by: str
    reason: Optional[str] = None