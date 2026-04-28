# arvis/reflexive/compliance/reflexive_compliance_chain.py

from dataclasses import dataclass
from typing import Dict, Any, Protocol

from arvis.reflexive.compliance.compliance_reflexive_attestation import (
    ComplianceReflexiveAttestation,
)


class SupportsToDict(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...


@dataclass(frozen=True)
class ReflexiveComplianceChain:
    """
    Deterministic compliance chain linking:
    - Reflexive snapshot (opaque)
    - Declarative explanation
    - Cryptographic attestation
    """

    snapshot: SupportsToDict
    explanation: Any

    def to_dict(self) -> Dict[str, Any]:
        snapshot_dict = self.snapshot.to_dict()
        explanation_dict = self.explanation.to_dict()
        attestation = ComplianceReflexiveAttestation.from_explanation(explanation_dict)

        return {
            "snapshot": snapshot_dict,
            "explanation": explanation_dict,
            "attestation": attestation.to_dict(),
            "compliance": {
                "version": "B15",
                "deterministic": True,
                "zkcs": True,
            },
        }
