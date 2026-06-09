# arvis/telemetry/adapters/__init__.py
"""
Adapters that build telemetry events from public domain contracts.

Adapters are the only telemetry components allowed to depend on domain
types, and they depend only on *public* contracts (never cognition
internals). They are kept out of ``arvis.telemetry`` top-level exports so
that importing the telemetry core never pulls in domain packages.
"""

from arvis.telemetry.adapters.stability import (
    STABILITY_COMPONENT,
    stability_event,
)

__all__ = [
    "STABILITY_COMPONENT",
    "stability_event",
]
