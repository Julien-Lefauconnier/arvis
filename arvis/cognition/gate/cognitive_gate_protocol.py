# arvis/cognition/gate/cognitive_gate_protocol.py

from typing import Protocol

from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot

from .cognitive_gate_result import CognitiveGateResult


class CognitiveGate(Protocol):
    def evaluate(self, bundle: CognitiveBundleSnapshot) -> CognitiveGateResult: ...
