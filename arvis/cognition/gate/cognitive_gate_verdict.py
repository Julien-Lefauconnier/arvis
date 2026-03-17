# arvis/cognition/gate/cognitive_gate_verdict.py

from enum import Enum


class CognitiveGateVerdict(str, Enum):
    ALLOW = "allow"
    REQUIRE_CONFIRMATION = "require_confirmation"
    ABSTAIN = "abstain"
