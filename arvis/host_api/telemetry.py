# arvis/host_api/telemetry.py

"""Observing a run.

The in-memory sink a host hands to the engine and the event kinds
it reads back.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.telemetry import (
    InMemoryTelemetrySink,
    TelemetryKind,
)

__all__ = [
    "InMemoryTelemetrySink",
    "TelemetryKind",
]
