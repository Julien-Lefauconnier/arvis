# tests/telemetry/test_telemetry_sink.py

from threading import Thread

from arvis.telemetry import (
    InMemoryTelemetrySink,
    NullTelemetrySink,
    TelemetryEvent,
    TelemetryKind,
    TelemetryLevel,
    TelemetrySink,
)


def _event(seq: int) -> TelemetryEvent:
    return TelemetryEvent.create(
        kind=TelemetryKind.LIFECYCLE,
        component="kernel.pipeline",
        message="stage finished",
        level=TelemetryLevel.DEBUG,
        sequence=seq,
    )


def test_null_sink_is_noop() -> None:
    sink = NullTelemetrySink()
    assert sink.emit(_event(1)) is None


def test_inmemory_sink_appends_in_order() -> None:
    sink = InMemoryTelemetrySink()
    sink.emit(_event(1))
    sink.emit(_event(2))
    recorded = sink.events()
    assert [e.sequence for e in recorded] == [1, 2]
    assert len(sink) == 2


def test_inmemory_sink_returns_defensive_copy() -> None:
    sink = InMemoryTelemetrySink()
    sink.emit(_event(1))
    snapshot = sink.events()
    snapshot.clear()
    assert len(sink) == 1


def test_inmemory_sink_clear() -> None:
    sink = InMemoryTelemetrySink()
    sink.emit(_event(1))
    sink.clear()
    assert len(sink) == 0
    assert list(sink) == []


def test_inmemory_sink_is_iterable() -> None:
    sink = InMemoryTelemetrySink()
    sink.emit(_event(1))
    sink.emit(_event(2))
    assert [e.sequence for e in sink] == [1, 2]


def test_sinks_satisfy_protocol() -> None:
    assert isinstance(NullTelemetrySink(), TelemetrySink)
    assert isinstance(InMemoryTelemetrySink(), TelemetrySink)


def test_inmemory_sink_is_thread_safe() -> None:
    sink = InMemoryTelemetrySink()
    per_thread = 200
    threads = [
        Thread(target=lambda: [sink.emit(_event(i)) for i in range(per_thread)])
        for _ in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(sink) == per_thread * 8
