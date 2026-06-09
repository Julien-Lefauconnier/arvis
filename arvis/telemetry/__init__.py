# arvis/telemetry/__init__.py
"""
Telemetry layer.

Deterministic, replay-safe telemetry contract for ARVIS.

The cognitive core builds immutable :class:`TelemetryEvent` values that
describe boundary-worthy occurrences (lifecycle, stability, decision,
degradation, error, escalation) and hands them to a :class:`TelemetrySink`.
Sinks are the only component allowed to perform IO; the core never logs
directly. Identity is content-addressed and wall-clock-independent, so
telemetry is consistent under replay.
"""

from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.sink import (
    InMemoryTelemetrySink,
    NullTelemetrySink,
    TelemetrySink,
)
from arvis.telemetry.types import (
    TelemetryAttributes,
    TelemetryPayload,
    TelemetryPrimitive,
    TelemetryValue,
)

__all__ = [
    "TelemetryEvent",
    "TelemetryKind",
    "TelemetryLevel",
    "TelemetrySink",
    "NullTelemetrySink",
    "InMemoryTelemetrySink",
    "TelemetryAttributes",
    "TelemetryPayload",
    "TelemetryPrimitive",
    "TelemetryValue",
]
