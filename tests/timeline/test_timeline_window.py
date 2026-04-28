# tests/timeline/test_timeline_window.py

from datetime import UTC, datetime, timedelta

import pytest

from arvis.timeline.timeline_window import TimelineWindow


def test_window_creation():
    now = datetime.now(UTC)

    w = TimelineWindow(after=now)

    assert w.after == now
    assert w.before is None


def test_window_valid_range():
    now = datetime.now(UTC)
    later = now + timedelta(seconds=10)

    w = TimelineWindow(after=now, before=later)

    assert w.after == now
    assert w.before == later


def test_window_invalid_range():
    now = datetime.now(UTC)
    earlier = now - timedelta(seconds=10)

    with pytest.raises(ValueError):
        TimelineWindow(after=now, before=earlier)


def test_window_to_dict():
    now = datetime.now(UTC)
    later = now + timedelta(seconds=5)

    w = TimelineWindow(after=now, before=later)

    d = w.to_dict()

    assert d["after"] == now.isoformat()
    assert d["before"] == later.isoformat()


def test_window_to_dict_partial():
    now = datetime.now(UTC)

    w = TimelineWindow(after=now)

    d = w.to_dict()

    assert d["after"] == now.isoformat()
    assert d["before"] is None


def test_window_ordering():
    now = datetime.now(UTC)

    w1 = TimelineWindow(after=now)
    w2 = TimelineWindow(after=now + timedelta(seconds=5))

    assert w1 < w2


def test_window_ordering_none_after():
    now = datetime.now(UTC)

    w1 = TimelineWindow()
    w2 = TimelineWindow(after=now)

    assert w1 < w2


def test_window_immutable():
    w = TimelineWindow()

    with pytest.raises(AttributeError):
        w.after = datetime.now(UTC)
