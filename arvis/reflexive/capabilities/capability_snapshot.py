# arvis/reflexive/capabilities/capability_snapshot.py

from dataclasses import dataclass
from typing import Tuple, Dict, Any

from arvis.reflexive.capabilities.capability import Capability


@dataclass(frozen=True)
class CapabilitySnapshot:
    version: str
    generated_from: str
    capabilities: Tuple[Capability, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "generated_from": self.generated_from,
            "capabilities": [
                {
                    "key": cap.key,
                    "description": cap.description,
                    "enabled": cap.enabled,
                    "limits": list(cap.limits),
                }
                for cap in self.capabilities
            ],
        }
