# arvis/telemetry/event.py

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from arvis.telemetry.types import TelemetryAttributes, TelemetryPayload
from arvis.types.timestamps import utcnow


class TelemetryKind(StrEnum):
    LIFECYCLE = "lifecycle"
    STABILITY = "stability"
    DECISION = "decision"
    DEGRADATION = "degradation"
    ERROR = "error"
    ESCALATION = "escalation"


class TelemetryLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(slots=True, frozen=True)
class TelemetryEvent:
    """
    Immutable, replay-safe telemetry record.

    A telemetry event describes *what happened* at a boundary worth
    observing in a cognitive run (lifecycle, stability verdict, decision,
    degradation, error, escalation).

    Design contract:
    - the event carries no chain-of-thought and no raw cognitive content;
      ``message`` is a short non-inferential descriptor and ``attributes``
      hold structured, ZKCS-safe values (scores, regimes, counters)
    - identity (``fingerprint`` / ``event_id``) is content-addressed over
      the deterministic fields only; the wall-clock ``emitted_at`` and the
      ``monotonic_ns`` reading are recorded for audit but never enter
      identity, so a faithful replay yields identical ids
    """

    kind: TelemetryKind
    level: TelemetryLevel
    component: str
    message: str
    attributes: TelemetryAttributes = field(default_factory=dict)
    sequence: int | None = None
    emitted_at: datetime = field(default_factory=utcnow)
    monotonic_ns: int | None = None
    replay_safe: bool = True
    sensitive: bool = False

    fingerprint: str = field(default="", init=False)
    event_id: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if not self.component:
            raise ValueError("TelemetryEvent.component must be non-empty")

        fingerprint = self._compute_fingerprint()
        object.__setattr__(self, "fingerprint", fingerprint)

        if self.sequence is None:
            event_id = fingerprint
        else:
            digest = hashlib.sha256(f"{fingerprint}:{self.sequence}".encode())
            event_id = digest.hexdigest()

        object.__setattr__(self, "event_id", event_id)

    def _compute_fingerprint(self) -> str:
        canonical = {
            "kind": self.kind.value,
            "level": self.level.value,
            "component": self.component,
            "message": self.message,
            "attributes": self.attributes,
        }
        serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()

    @property
    def timestamp(self) -> datetime:
        """Canonical temporal accessor for unified-timeline consumers."""
        return self.emitted_at

    @classmethod
    def create(
        cls,
        *,
        kind: TelemetryKind,
        component: str,
        message: str,
        level: TelemetryLevel = TelemetryLevel.INFO,
        attributes: TelemetryAttributes | None = None,
        sequence: int | None = None,
        emitted_at: datetime | None = None,
        monotonic_ns: int | None = None,
        replay_safe: bool = True,
        sensitive: bool = False,
    ) -> TelemetryEvent:
        """
        Preferred constructor.

        Fills ``emitted_at`` with the current UTC time and ``monotonic_ns``
        with a monotonic reading when not supplied. Both remain outside the
        event identity.
        """
        return cls(
            kind=kind,
            level=level,
            component=component,
            message=message,
            attributes=dict(attributes) if attributes is not None else {},
            sequence=sequence,
            emitted_at=emitted_at if emitted_at is not None else utcnow(),
            monotonic_ns=(
                monotonic_ns if monotonic_ns is not None else time.monotonic_ns()
            ),
            replay_safe=replay_safe,
            sensitive=sensitive,
        )

    def to_dict(self) -> TelemetryPayload:
        """Serializable, structurally stable view of the event."""
        return {
            "kind": self.kind.value,
            "level": self.level.value,
            "component": self.component,
            "message": self.message,
            "attributes": dict(self.attributes),
            "sequence": self.sequence,
            "emitted_at": self.emitted_at.isoformat(),
            "monotonic_ns": self.monotonic_ns,
            "replay_safe": self.replay_safe,
            "sensitive": self.sensitive,
            "fingerprint": self.fingerprint,
            "event_id": self.event_id,
        }
