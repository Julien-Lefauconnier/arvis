# arvis/telemetry/adapters/stability.py

from __future__ import annotations

from arvis.stability.stability_snapshot import StabilitySnapshot
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

STABILITY_COMPONENT = "kernel.stability"


def stability_event(
    snapshot: StabilitySnapshot,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = STABILITY_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """
    Build a STABILITY telemetry event from the public stability snapshot.

    Maps the OS-level :class:`StabilitySnapshot` contract onto a telemetry
    event whose attributes carry the real stability mathematics (Lyapunov
    level, collapse risk, drift statistics, instability rate). Those values
    let a consumer understand the stability verdict without reconstructing
    any reasoning (ZKCS-safe).

    The telemetry ``level`` is supplied by the caller rather than inferred
    from a threshold: ARVIS does not encode magic thresholds, and the
    appropriate severity is a decision the gating context already owns.
    """
    attributes: TelemetryAttributes = {
        "verdict": snapshot.verdict,
        "score": snapshot.score,
        "confidence": snapshot.confidence,
        "samples": snapshot.samples,
        "mean_dv": snapshot.mean_dv,
        "std_dv": snapshot.std_dv,
        "instability_rate": snapshot.instability_rate,
        "collapse_risk": snapshot.collapse_risk,
        "last_v": snapshot.last_v,
        "reasons": [reason for reason in snapshot.reasons],
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="stability snapshot",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
