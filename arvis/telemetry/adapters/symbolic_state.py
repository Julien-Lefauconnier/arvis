# arvis/telemetry/adapters/symbolic_state.py

from __future__ import annotations

from arvis.math.state.symbolic_state import SymbolicState
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes, TelemetryValue

SYMBOLIC_STATE_COMPONENT = "kernel.symbolic_state"


def symbolic_state_event(
    snapshot: SymbolicState,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = SYMBOLIC_STATE_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a telemetry event from the symbolic state snapshot.

    ``SymbolicState`` captures the discrete cognitive posture: the resolved
    intent and its confidence, the gate verdict, the conversation mode, the
    conflict histogram and severity, and override statistics. All values are
    deterministic and ZKCS-safe.
    """
    histogram: dict[str, TelemetryValue] = {
        key: count for key, count in snapshot.conflict_histogram.items()
    }
    attributes: TelemetryAttributes = {
        "intent_type": snapshot.intent_type,
        "intent_confidence": snapshot.intent_confidence,
        "gate_verdict": snapshot.gate_verdict,
        "conversation_mode": snapshot.conversation_mode,
        "conflict_histogram": histogram,
        "conflict_severity": snapshot.conflict_severity,
        "override_count": snapshot.override_count,
        "override_rate": snapshot.override_rate,
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="symbolic state snapshot",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
