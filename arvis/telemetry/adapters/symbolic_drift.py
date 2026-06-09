# arvis/telemetry/adapters/symbolic_drift.py

from __future__ import annotations

from arvis.cognition.observability.symbolic.symbolic_drift_snapshot import (
    SymbolicDriftSnapshot,
)
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

SYMBOLIC_DRIFT_COMPONENT = "kernel.symbolic_drift"


def symbolic_drift_event(
    snapshot: SymbolicDriftSnapshot,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = SYMBOLIC_DRIFT_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a telemetry event from the symbolic drift snapshot.

    ``SymbolicDriftSnapshot`` tracks movement in the discrete symbolic layer:
    the drift score and regime, intent/gate switches, the confidence and
    conflict deltas, and the override rate. All values are deterministic and
    ZKCS-safe.
    """
    attributes: TelemetryAttributes = {
        "drift_score": snapshot.drift_score,
        "regime": snapshot.regime.value,
        "intent_switch": snapshot.intent_switch,
        "gate_switch": snapshot.gate_switch,
        "confidence_delta": snapshot.confidence_delta,
        "conflict_delta": snapshot.conflict_delta,
        "override_rate": snapshot.override_rate,
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="symbolic drift snapshot",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
