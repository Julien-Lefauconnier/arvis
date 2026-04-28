# arvis/reflexive/compliance/compliance_reflexive_attestation.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComplianceReflexiveAttestation:
    """
    Explicit reflexive attestation.

    This object:
    - is deterministic
    - is read-only
    - contains no cognitive data
    - can be verified externally
    """

    fingerprint: str
    scope: str
    authority: str
    deterministic: bool
    immutability: bool

    @classmethod
    def from_explanation(
        cls, explanation_dict: dict[str, Any]
    ) -> "ComplianceReflexiveAttestation":
        """
        Extract attestation data from a reflexive explanation.
        """
        att = explanation_dict.get("attestation", {})

        return cls(
            fingerprint=att.get("fingerprint"),
            scope=att.get("scope"),
            authority=att.get("authority"),
            deterministic=bool(att.get("deterministic")),
            immutability=bool(att.get("immutability")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "scope": self.scope,
            "authority": self.authority,
            "deterministic": self.deterministic,
            "immutability": self.immutability,
        }
