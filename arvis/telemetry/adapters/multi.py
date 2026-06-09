# arvis/telemetry/adapters/multi.py

from __future__ import annotations

from arvis.math.observability.multi_horizon_snapshot import MultiHorizonSnapshot
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

MULTI_HORIZON_COMPONENT = "kernel.multi"


def multi_horizon_event(
    snapshot: MultiHorizonSnapshot,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = MULTI_HORIZON_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a telemetry event from the multi-horizon stability snapshot.

    ``MultiHorizonSnapshot`` aggregates collapse risk across horizons into a
    single stability confidence and an early-warning flag, with an optional
    mode hint. All values are deterministic and ZKCS-safe.
    """
    attributes: TelemetryAttributes = {
        "collapse_risk": snapshot.collapse_risk,
        "stability_confidence": snapshot.stability_confidence,
        "early_warning": snapshot.early_warning,
        "mode_hint": snapshot.mode_hint,
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="multi-horizon snapshot",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
