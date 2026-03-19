# tests/timeline/test_timeline_delta_edges.py

import pytest

from arvis.timeline.timeline_delta import (
    TimelineDelta,
    TimelineDeltaError,
    TimelineDeltaBaseMismatch,
)
from arvis.timeline.timeline_cursor import TimelineCursor
from datetime import datetime, timezone


class DummyEntry:
    def __init__(self, i):
        self.entry_id = str(i)


class DummySnap:
    def __init__(self, cursor):
        self._cursor = cursor
        self.entries = []

    def cursor(self):
        return self._cursor

    def append(self, e):
        self.entries.append(e)
        return self


def make_cursor(n):
    return TimelineCursor(
        timestamp=datetime.now(timezone.utc),
        head="a" * 64 if n > 0 else None,
        total_entries=n,
    )


def test_none_snapshot_apply():
    delta = TimelineDelta(
        base=make_cursor(0),
        target=make_cursor(1),
        entries=(DummyEntry(1),),
    )

    with pytest.raises(TimelineDeltaError):
        delta.apply_to(None)


def test_base_mismatch():
    delta = TimelineDelta(
        base=make_cursor(0),
        target=make_cursor(1),
        entries=(DummyEntry(1),),
    )

    snap = DummySnap(make_cursor(1))

    with pytest.raises(TimelineDeltaBaseMismatch):
        delta.apply_to(snap)


def test_verify_target_mismatch():
    base = make_cursor(0)
    target = make_cursor(1)

    delta = TimelineDelta(
        base=base,
        target=target,
        entries=(DummyEntry(1),),
    )

    # snapshot volontairement incohérent
    bad_snapshot = DummySnap(make_cursor(999))

    with pytest.raises(Exception):
        delta.verify_against(bad_snapshot)