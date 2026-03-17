# arvis/cognition/gate/cognitive_gate_result.py

from dataclasses import dataclass
from .cognitive_gate_verdict import CognitiveGateVerdict


@dataclass(frozen=True)
class CognitiveGateResult:
    verdict: CognitiveGateVerdict
    reason: str | None
    bundle_id: str