# arvis/signals/canonical/specs/timeline.py
"""
Canonical Signal Specifications — Timeline Domain — Closed Canonical World
"""

from arvis.signals.canonical.canonical_signal_category import CanonicalSignalCategory
from arvis.signals.canonical.canonical_signal_key import CanonicalSignalKey
from arvis.signals.canonical.canonical_signal_registry import (
    CanonicalSignalRegistry,
    CanonicalSignalSpec,
)


def register_timeline_signals() -> None:
    """Register all timeline-related canonical signals."""

    # MEMORY_LONG_PROJECTED
    CanonicalSignalRegistry.register(
        CanonicalSignalSpec(
            key=CanonicalSignalKey(
                category=CanonicalSignalCategory.TEMPORAL_STATE,
                code="memory_long_projected",
            ),
            states_allowed=frozenset(["PROJECTED", "ACTIVE", "SUPERSEDED"]),
            subject_kinds=frozenset(["timeline:entry"]),
            origin_allowed=frozenset(["timeline"]),
        )
    )

    # GHOST_SIGNAL
    CanonicalSignalRegistry.register(
        CanonicalSignalSpec(
            key=CanonicalSignalKey(
                category=CanonicalSignalCategory.TEMPORAL_STATE,
                code="ghost_signal",
            ),
            states_allowed=frozenset(["GHOST"]),
            subject_kinds=frozenset(["timeline:entry"]),
            origin_allowed=frozenset(["timeline"]),
        )
    )
