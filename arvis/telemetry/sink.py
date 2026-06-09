# arvis/telemetry/sink.py

from __future__ import annotations

from _thread import LockType
from collections.abc import Iterator
from threading import Lock
from typing import Protocol, runtime_checkable

from arvis.telemetry.event import TelemetryEvent


@runtime_checkable
class TelemetrySink(Protocol):
    """
    Boundary contract for telemetry emission.

    A sink is the only component allowed to perform IO for telemetry. The
    cognitive core constructs immutable :class:`TelemetryEvent` values and
    hands them to a sink; the core itself never logs, writes, or blocks.

    Implementations MUST isolate their side effects and MUST NOT raise back
    into the caller for routine emission failures: telemetry is never
    allowed to break cognition.
    """

    def emit(self, event: TelemetryEvent) -> None:
        """Record or forward a single telemetry event."""
        ...


class NullTelemetrySink:
    """
    Default no-op sink.

    Drops every event. Used when telemetry is disabled, inside pure
    deterministic contexts, and as a fail-safe default so the absence of a
    configured sink can never affect cognition.
    """

    def emit(self, event: TelemetryEvent) -> None:
        return None


class InMemoryTelemetrySink:
    """
    Append-only, thread-safe, deterministic in-memory sink.

    Intended for tests, replay verification, and local introspection.
    Reads return defensive copies to prevent external mutation.
    """

    def __init__(self) -> None:
        self._events: list[TelemetryEvent] = []
        self._lock: LockType = Lock()

    def emit(self, event: TelemetryEvent) -> None:
        with self._lock:
            self._events.append(event)

    def events(self) -> list[TelemetryEvent]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)

    def __iter__(self) -> Iterator[TelemetryEvent]:
        return iter(self.events())
