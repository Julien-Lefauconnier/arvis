# arvis/ir/gate.py

from dataclasses import dataclass
from enum import Enum


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