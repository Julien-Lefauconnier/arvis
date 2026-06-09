# arvis/telemetry/adapters/stats.py

from __future__ import annotations

from arvis.math.observability.stability_stats_snapshot import StabilityStatsSnapshot
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

STATS_COMPONENT = "kernel.stats"


def stats_event(
    snapshot: StabilityStatsSnapshot,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = STATS_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a telemetry event from the stability statistics snapshot.

    ``StabilityStatsSnapshot`` summarises the trajectory statistics over the
    observed timeline: the mean delta, contraction rate, instability rate and
    the number of samples. All values are deterministic and ZKCS-safe.
    """
    attributes: TelemetryAttributes = {
        "mean_delta": snapshot.mean_delta,
        "contraction_rate": snapshot.contraction_rate,
        "instability_rate": snapshot.instability_rate,
        "samples": snapshot.samples,
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="stability stats snapshot",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
