# arvis/reflexive/capabilities/capability_snapshot_builder.py

from arvis.reflexive.capabilities.capability_registry import (
    CapabilityRegistry,
)
from arvis.reflexive.capabilities.capability_snapshot import (
    CapabilitySnapshot,
)


def build_capability_snapshot() -> CapabilitySnapshot:
    capabilities = CapabilityRegistry.list_capabilities()

    # Canonical ordering
    capabilities_sorted = tuple(sorted(capabilities, key=lambda c: c.key))

    return CapabilitySnapshot(
        version="1.0",
        generated_from="registry",
        capabilities=capabilities_sorted,
    )
