# tests/types/test_timestamps.py

from datetime import UTC

from arvis.types.timestamps import utcnow


def test_utcnow_returns_datetime():
    ts = utcnow()

    assert ts is not None
    assert ts.tzinfo is not None


def test_utcnow_is_utc():
    ts = utcnow()

    assert ts.tzinfo == UTC


def test_utcnow_monotonic():
    t1 = utcnow()
    t2 = utcnow()

    assert t2 >= t1
