# arvis/cognition/gate/cognitive_gate_verdict.py

from enum import StrEnum


class CognitiveGateVerdict(StrEnum):
    ALLOW = "allow"
    REQUIRE_CONFIRMATION = "require_confirmation"
    ABSTAIN = "abstain"
