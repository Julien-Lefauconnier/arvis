# arvis/reasoning/reasoning_gap.py

from dataclasses import dataclass
from enum import StrEnum


class GapType(StrEnum):
    UNKNOWN_KNOWLEDGE = "unknown_knowledge"
    UNCERTAIN_KNOWLEDGE = "uncertain_knowledge"
    MISSING_CONTEXT = "missing_context"
    AMBIGUOUS_INTENT = "ambiguous_intent"


class GapOrigin(StrEnum):
    KNOWLEDGE = "knowledge"
    CONTEXT = "context"
    USER = "user"
    SYSTEM = "system"


class GapSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ReasoningGap:
    """
    Declarative observation of a missing reasoning element.

    Kernel guarantees:
    - no decision
    - no action
    - pure observation
    """

    gap_type: GapType
    origin: GapOrigin
    severity: GapSeverity
    description: str
    origin_ref: str | None = None
