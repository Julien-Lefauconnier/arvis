# arvis/adapters/kernel/__init__.py

from arvis.signals.canonical.canonical_signal_registry import (
    CanonicalSignalRegistry,
    register_all_canonical_signals,
)


def bootstrap_kernel_adapters() -> None:
    if not CanonicalSignalRegistry.all():
        register_all_canonical_signals()


bootstrap_kernel_adapters()

__all__ = [
    "bootstrap_kernel_adapters",
]
