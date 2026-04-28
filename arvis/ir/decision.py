# arvis/ir/decision.py

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

# ---------------------------
# Sub-components
# ---------------------------


@dataclass(frozen=True)
class CognitiveActionIR:
    action_id: str
    category: str
    severity: str  # safe / confirm / critical
    requires_confirmation: bool = False
    parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CognitiveGapIR:
    gap_type: str
    severity: str
    description: str


@dataclass(frozen=True)
class CognitiveConflictIR:
    conflict_type: str
    severity: str
    description: str
    resolvable_by_confirmation: bool = True


@dataclass(frozen=True)
class CognitiveKnowledgeIR:
    state: str  # known / partial / unknown / conflicted
    support_level: float | None = None


@dataclass(frozen=True)
class CognitiveUncertaintyIR:
    axis: str
    level: float  # normalized [0,1]
    explanation: str | None = None


# ---------------------------
# Main decision object
# ---------------------------


@dataclass(frozen=True)
class CognitiveDecisionIR:
    decision_id: str

    decision_kind: (
        str  # conversational / informational / action / memory / meta / unknown
    )
    memory_intent: str  # none / candidate / explicit / required

    reason_codes: tuple[str, ...] = ()

    proposed_actions: tuple[CognitiveActionIR, ...] = ()
    gaps: tuple[CognitiveGapIR, ...] = ()
    conflicts: tuple[CognitiveConflictIR, ...] = ()

    reasoning_intents: tuple[str, ...] = ()

    uncertainty_frames: tuple[CognitiveUncertaintyIR, ...] = ()
    knowledge: CognitiveKnowledgeIR | None = None

    context_hints: Mapping[str, Any] = field(default_factory=dict)
