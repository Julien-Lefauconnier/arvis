# arvis/telemetry/adapters/tension.py

from __future__ import annotations

from arvis.math.signals.system_tension import SystemTensionSignal
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

SYSTEM_TENSION_COMPONENT = "kernel.system_tension"


def system_tension_event(
    tension: SystemTensionSignal,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = SYSTEM_TENSION_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a telemetry event from the unified system-tension signal.

    ``SystemTensionSignal`` fuses the three instability axes — collapse
    (physical), drift (dynamic) and conflict (cognitive) — into one signal.
    The attributes carry the raw axes plus the derived level, dominant axis
    and high-tension flag, all deterministic and ZKCS-safe.
    """
    attributes: TelemetryAttributes = {
        "collapse": tension.collapse,
        "drift": tension.drift,
        "conflict": tension.conflict,
        "level": tension.level(),
        "dominant_axis": tension.dominant_axis(),
        "is_high": tension.is_high(),
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="system tension signal",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
