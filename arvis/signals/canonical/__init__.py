# arvis/signals/canonical/__init__.py

from .canonical_signal import CanonicalSignal
from .canonical_signal_registry import (
    CanonicalSignalRegistry,
    register_all_canonical_signals,
)
from .canonical_signal_key import CanonicalSignalKey
from .canonical_signal_spec import CanonicalSignalSpec
from .canonical_signal_category import CanonicalSignalCategory

# Auto-bootstrap registry
register_all_canonical_signals()
CanonicalSignalRegistry.freeze()

__all__ = [
    "CanonicalSignal",
    "CanonicalSignalRegistry",
    "CanonicalSignalKey",
    "CanonicalSignalSpec",
    "CanonicalSignalCategory",
]
