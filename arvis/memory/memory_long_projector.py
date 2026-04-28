# arvis/memory/memory_long_projector.py

from typing import Any

from arvis.memory.memory_long_snapshot import (
    MemoryLongSnapshot,
)


class MemoryLongContextProjector:
    """
    Projects long-term declarative memory into cognition-safe signals.

    ZKCS invariant:
    - no ciphertext access
    - no payload reconstruction
    - only key-level declarative projection
    """

    def project(self, snapshot: MemoryLongSnapshot) -> dict[str, Any]:
        #  Extract declarative keys only
        keys = {e.key for e in snapshot.active_entries}

        #  Declarative-only: preference presence signals
        preferences = {
            "language": "language" in keys,
            "timezone": "timezone" in keys,
        }

        #  Declarative constraint flags
        constraints = [k for k in keys if k.startswith("no_")]

        return {
            "constraints": constraints,
            "preferences": preferences,
            "has_timezone": preferences["timezone"],
            "has_language_pref": preferences["language"],
            "memory_pressure": len(keys),
            "has_constraints": len(constraints) > 0,
            # --------------------------------------------
            # TEMPORAL MEMORY PLACEHOLDER
            # --------------------------------------------
            # will be refined by conversation layer
            "memory_instability": min(len(keys) / 10.0, 1.0),
        }
