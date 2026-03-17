# tests/timeline/test_timeline_window.py

import pytest
from datetime import datetime, timezone, timedelta

from arvis.timeline.timeline_window import TimelineWindow


def test_window_creation():

    now = datetime.now(timezone.utc)

    w = TimelineWindow(after=now)

    assert w.after == now
    assert w.before is None


def test_window_valid_range():

    now = datetime.now(timezone.utc)
    later = now + timedelta(seconds=10)

    w = TimelineWindow(after=now, before=later)

    assert w.after == now
    assert w.before == later


def test_window_invalid_range():

    now = datetime.now(timezone.utc)
    earlier = now - timedelta(seconds=10)

    with pytest.raises(ValueError):

        TimelineWindow(after=now, before=earlier)


def test_window_to_dict():

    now = datetime.now(timezone.utc)
    later = now + timedelta(seconds=5)

    w = TimelineWindow(after=now, before=later)

    d = w.to_dict()

    assert d["after"] == now.isoformat()
    assert d["before"] == later.isoformat()


def test_window_to_dict_partial():

    now = datetime.now(timezone.utc)

    w = TimelineWindow(after=now)

    d = w.to_dict()

    assert d["after"] == now.isoformat()
    assert d["before"] is None


def test_window_ordering():

    now = datetime.now(timezone.utc)

    w1 = TimelineWindow(after=now)
    w2 = TimelineWindow(after=now + timedelta(seconds=5))

    assert w1 < w2


def test_window_ordering_none_after():

    now = datetime.now(timezone.utc)

    w1 = TimelineWindow()
    w2 = TimelineWindow(after=now)

    assert w1 < w2


def test_window_immutable():

    w = TimelineWindow()

    with pytest.raises(Exception):
        w.after = datetime.now(timezone.utc)