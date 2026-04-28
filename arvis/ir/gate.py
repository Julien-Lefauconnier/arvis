# arvis/ir/gate.py

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class CognitiveGateTraceStepIR:
    stage: str
    before: str
    after: str
    reason_codes: tuple[str, ...]
    severity: float = 0.0
    stability_impact: float = 0.0


class CognitiveGateVerdictIR(str, Enum):
    ALLOW = "allow"
    REQUIRE_CONFIRMATION = "require_confirmation"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class CognitiveGateIR:
    verdict: CognitiveGateVerdictIR
    bundle_id: str
    reason_codes: tuple[str, ...]
    risk_level: float | None = None
    triggered_rules: tuple[str, ...] = ()
    decision_trace: tuple[CognitiveGateTraceStepIR, ...] = ()
    total_severity: float | None = None
    max_severity: float | None = None
    instability_score: float | None = None
