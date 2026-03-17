# tests/timeline/test_timeline_delta.py

from datetime import datetime, timezone
import pytest

from arvis.timeline.timeline_delta import (
    TimelineDelta,
    TimelineDeltaError,
    TimelineDeltaEmptyError,
    TimelineDeltaBaseMismatch,
    TimelineDeltaTargetMismatch,
)

from arvis.timeline.timeline_snapshot import TimelineSnapshot
from arvis.timeline.timeline_entry import TimelineEntry, TimelineEntryNature
from arvis.timeline.timeline_types import TimelineEntryType


# ---------------------------------------------------------
# helpers
# ---------------------------------------------------------

def make_entry(i: int) -> TimelineEntry:
    return TimelineEntry.unsafe(
        entry_id=f"entry{i:04d}",
        type=TimelineEntryType.SYSTEM_NOTICE,
        title=f"entry {i}",
        description=None,
        action_id=None,
        created_at=datetime.now(timezone.utc),
    )


def make_snapshot(n: int) -> TimelineSnapshot:
    entries = [make_entry(i) for i in range(n)]
    return TimelineSnapshot.build(entries)


# ---------------------------------------------------------
# basic delta creation
# ---------------------------------------------------------

def test_delta_from_snapshots_basic():

    base = make_snapshot(2)
    target = make_snapshot(5)

    delta = TimelineDelta.from_snapshots(base, target)

    assert delta.size() == 3
    assert delta.base.total_entries == 2
    assert delta.target.total_entries == 5


# ---------------------------------------------------------
# delta empty detection
# ---------------------------------------------------------

def test_delta_empty_error():

    snap = make_snapshot(3)

    with pytest.raises(TimelineDeltaEmptyError):
        TimelineDelta.from_snapshots(snap, snap)


# ---------------------------------------------------------
# rollback detection
# ---------------------------------------------------------

def test_delta_rollback_error():

    base = make_snapshot(5)
    target = make_snapshot(2)

    with pytest.raises(TimelineDeltaError):
        TimelineDelta.from_snapshots(base, target)


# ---------------------------------------------------------
# apply delta
# ---------------------------------------------------------

def test_apply_delta():

    base = make_snapshot(2)

    target = base
    target = target.append(make_entry(2))
    target = target.append(make_entry(3))

    delta = TimelineDelta.from_snapshots(base, target)

    result = delta.apply_to(base)

    assert result.cursor() == target.cursor()
    assert len(result.entries) == 4


# ---------------------------------------------------------
# apply mismatch
# ---------------------------------------------------------

def test_apply_base_mismatch():

    base = make_snapshot(2)
    target = make_snapshot(4)
    other = make_snapshot(3)

    delta = TimelineDelta.from_snapshots(base, target)

    with pytest.raises(TimelineDeltaBaseMismatch):
        delta.apply_to(other)


# ---------------------------------------------------------
# verify
# ---------------------------------------------------------

def test_verify_against():

    base = make_snapshot(2)
    target = make_snapshot(4)

    delta = TimelineDelta.from_snapshots(base, target)

    delta.verify_against(base)


def test_verify_mismatch():

    base = make_snapshot(2)
    target = make_snapshot(4)
    other = make_snapshot(3)

    delta = TimelineDelta.from_snapshots(base, target)

    with pytest.raises(TimelineDeltaBaseMismatch):
        delta.verify_against(other)


# ---------------------------------------------------------
# duplicate entries protection
# ---------------------------------------------------------

def test_duplicate_entries_rejected():

    e = make_entry(1)

    base = make_snapshot(1)
    target = make_snapshot(2)

    with pytest.raises(TimelineDeltaError):
        TimelineDelta(
            base=base.cursor(),
            target=target.cursor(),
            entries=(e, e),
        )


# ---------------------------------------------------------
# size helper
# ---------------------------------------------------------

def test_delta_size():

    base = make_snapshot(1)
    target = make_snapshot(4)

    delta = TimelineDelta.from_snapshots(base, target)

    assert delta.size() == 3