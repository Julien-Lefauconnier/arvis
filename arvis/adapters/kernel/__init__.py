# arvis/adapters/kernel/__init__.py

from arvis.signals.canonical.canonical_signal_registry import (
    CanonicalSignalRegistry,
    register_all_canonical_signals,
)

# Guard to avoid duplicate registration
if not CanonicalSignalRegistry.all():
    register_all_canonical_signals()
