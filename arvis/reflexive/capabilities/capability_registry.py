# arvis/reflexive/capabilities/capability_registry.py

from typing import List
from arvis.reflexive.capabilities.capability import Capability


class CapabilityRegistry:
    """
    Static registry of system capabilities.
    """

    @staticmethod
    def list_capabilities() -> List[Capability]:
        return [
            Capability(
                key="reflexive_snapshot",
                description="Expose a reflexive snapshot of the system state",
                enabled=True,
                limits=(
                    "no cognition",
                    "no reasoning",
                    "post-cognitive only",
                ),
            ),
            Capability(
                key="reflexive_attestation",
                description="Produce a deterministic attestation of exposed surfaces",
                enabled=True,
                limits=(
                    "structural integrity only",
                    "no truth validation",
                ),
            ),
        ]
