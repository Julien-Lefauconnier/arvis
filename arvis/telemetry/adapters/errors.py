# arvis/telemetry/adapters/errors.py

from __future__ import annotations

from collections.abc import Mapping

from arvis.errors.types import ErrorPayload
from arvis.telemetry.event import TelemetryEvent, TelemetryKind, TelemetryLevel
from arvis.telemetry.types import TelemetryAttributes

ERROR_COMPONENT = "kernel.errors"

_LEVELS: frozenset[str] = frozenset(level.value for level in TelemetryLevel)


def escalation_event(
    statistics: Mapping[str, int],
    *,
    level: TelemetryLevel = TelemetryLevel.WARNING,
    component: str = ERROR_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """
    Build an ESCALATION event from an ``ErrorManager`` statistics view.

    Attributes carry the deterministic error counters (total, fatal,
    error, degraded, fail_closed, ...) that justify an escalation, with no
    error content. The level defaults to WARNING because the event kind is
    itself the escalation signal; callers may raise it.
    """
    attributes: TelemetryAttributes = {key: value for key, value in statistics.items()}
    return TelemetryEvent.create(
        kind=TelemetryKind.ESCALATION,
        component=component,
        message="error escalation",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )


def degradation_event(
    degradation: Mapping[str, object],
    *,
    level: TelemetryLevel = TelemetryLevel.WARNING,
    component: str = ERROR_COMPONENT,
    sequence: int | None = None,
) -> TelemetryEvent:
    """
    Build a DEGRADATION event from an ``ErrorManager`` runtime-degradation
    view (``active`` / ``count`` / ``last_code`` / ``domains``).
    """
    last_code = degradation.get("last_code")
    raw_count = degradation.get("count", 0)
    count = raw_count if isinstance(raw_count, int) else 0
    raw_domains = degradation.get("domains")
    domains: dict[str, int] = {}
    if isinstance(raw_domains, Mapping):
        domains = {
            str(key): int(value)
            for key, value in raw_domains.items()
            if isinstance(value, int)
        }

    attributes: TelemetryAttributes = {
        "active": bool(degradation.get("active", False)),
        "count": count,
        "last_code": str(last_code) if last_code is not None else None,
        "domains": {key: value for key, value in domains.items()},
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.DEGRADATION,
        component=component,
        message="runtime degradation",
        level=level,
        attributes=attributes,
        sequence=sequence,
    )


def error_event(
    payload: ErrorPayload,
    *,
    component: str | None = None,
    sequence: int | None = None,
) -> TelemetryEvent:
    """
    Build an ERROR event from a single ``ArvisError`` payload.

    Only the deterministic classification is surfaced (code, domain,
    category, severity, policy, degraded, retryable, error fingerprint).
    Non-deterministic fields (``created_at``, ``monotonic_ns``,
    ``error_id``) and free-form ``details`` / ``traceback`` are
    deliberately excluded so the telemetry event stays replay-safe and
    ZKCS-safe; the error's own ``fingerprint`` is carried for correlation.

    The telemetry ``level`` is the direct correspondent of the error
    severity (an exhaustive enum-to-enum mapping, not a threshold).
    """
    severity = payload.get("severity")
    level = (
        TelemetryLevel(severity)
        if isinstance(severity, str) and severity in _LEVELS
        else TelemetryLevel.ERROR
    )
    resolved_component = component
    if resolved_component is None:
        domain = payload.get("domain")
        resolved_component = (
            domain if isinstance(domain, str) and domain else ERROR_COMPONENT
        )

    attributes: TelemetryAttributes = {
        "code": payload.get("code"),
        "domain": payload.get("domain"),
        "category": payload.get("category"),
        "severity": payload.get("severity"),
        "policy": payload.get("policy"),
        "degraded": payload.get("degraded"),
        "retryable": payload.get("retryable"),
        "error_fingerprint": payload.get("fingerprint"),
    }
    return TelemetryEvent.create(
        kind=TelemetryKind.ERROR,
        component=resolved_component,
        message="error captured",
        level=level,
        attributes=attributes,
        sequence=sequence,
        replay_safe=bool(payload.get("replay_safe", True)),
        sensitive=bool(payload.get("sensitive", False)),
    )
