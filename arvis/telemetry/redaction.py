# arvis/telemetry/redaction.py

from __future__ import annotations

from arvis.errors.redaction import redact_error_payload
from arvis.telemetry.event import TelemetryEvent
from arvis.telemetry.types import TelemetryPayload


def redacted_payload(
    event: TelemetryEvent,
    *,
    include_traceback: bool = False,
) -> TelemetryPayload:
    """
    Render a telemetry event as a redaction-safe payload.

    Redaction is a *representation* concern, never an identity one: the
    returned payload keeps the event's ``fingerprint`` and ``event_id``
    (computed over the true content) untouched, and only masks sensitive
    keys inside ``attributes``. The shared error redaction policy is reused
    so telemetry and error payloads mask identically (one ZKCS policy).
    """
    payload = event.to_dict()
    attributes = payload.get("attributes")
    if isinstance(attributes, dict):
        redacted = redact_error_payload(
            attributes,
            include_traceback=include_traceback,
        )
        payload["attributes"] = redacted
    return payload
