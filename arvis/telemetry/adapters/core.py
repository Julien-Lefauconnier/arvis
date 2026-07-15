# arvis/telemetry/adapters/core.py

from __future__ import annotations

from arvis.cognition.core.cognitive_core_result import CognitiveCoreResult
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

CORE_STABILITY_COMPONENT = "kernel.cognitive_core"


def _coerce_float(value: object) -> float | None:
    """Best-effort numeric coercion for telemetry attributes.

    Lyapunov projections may arrive either as plain numbers or as wrapper
    objects exposing a ``level()`` accessor. Anything else degrades to None
    rather than leaking a non-serializable object into the event.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    level = getattr(value, "level", None)
    if callable(level):
        try:
            return float(level())
        except Exception:  # arvis-broad: observe-only telemetry probe
            return None
    return None


def core_stability_event(
    core: CognitiveCoreResult,
    *,
    level: TelemetryLevel = TelemetryLevel.INFO,
    component: str = CORE_STABILITY_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """Build a STABILITY telemetry event from the cognitive core output.

    ``CognitiveCoreResult`` is the deterministic stability mathematics the
    core produces on every run (collapse risk, total drift, Lyapunov
    projections, regime). Unlike the richer observability ``StabilitySnapshot``
    — only built when observability is attached — this result is always
    present at the OS boundary, so it is the reliable telemetry source. The
    attributes are deterministic and carry no chain-of-thought (ZKCS-safe).
    """
    attributes: TelemetryAttributes = {
        "collapse_risk": _coerce_float(core.collapse_risk),
        "dv": _coerce_float(core.dv),
        "drift_score": _coerce_float(core.drift_score),
        "prev_lyap": _coerce_float(core.prev_lyap),
        "cur_lyap": _coerce_float(core.cur_lyap),
        "regime": core.regime,
        "stable": core.stable,
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.STABILITY,
        component=component,
        message="cognitive core stability",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )
