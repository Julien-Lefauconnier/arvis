# tests/timeline/test_snapshot_edges.py

import pytest
from datetime import datetime, timezone

from arvis.timeline.timeline_snapshot import TimelineSnapshot
from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_types import TimelineEntryType
from arvis.timeline.timeline_hashchain import TimelineHashChain


def make_entry(i: int) -> TimelineEntry:
    return TimelineEntry.unsafe(
        entry_id=f"id_{i:08d}",
        type=TimelineEntryType.SYSTEM_NOTICE,
        title=f"title_{i}",
        description=None,
        action_id=None,
        place_id=None,
        created_at=datetime.now(timezone.utc),
        device_id="0" * 64,
        lamport=i,
    )


def test_verify_failure(monkeypatch):
    snap = TimelineSnapshot.build([make_entry(0)])

    def broken(self, *args, **kwargs):
        raise ValueError

    monkeypatch.setattr(TimelineHashChain, "verify", broken)

    with pytest.raises(ValueError):
        snap.verify()


def test_empty_cursor():
    snap = TimelineSnapshot.build([])
    c = snap.cursor()

    assert c.total_entries == 0
    assert c.head is None