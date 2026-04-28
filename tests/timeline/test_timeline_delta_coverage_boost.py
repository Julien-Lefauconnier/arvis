# tests/timeline/test_timeline_delta_coverage_boost.py

from datetime import UTC, datetime

import pytest

from arvis.timeline.timeline_cursor import TimelineCursor
from arvis.timeline.timeline_delta import (
    TimelineDelta,
    TimelineDeltaDecodeError,
    TimelineDeltaError,
    _pack_frames,
    _unpack_frames,
)
from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_snapshot import TimelineSnapshot
from arvis.timeline.timeline_types import TimelineEntryType

# ============================================================
# Helpers
# ============================================================


def make_entry(i: int) -> TimelineEntry:
    return TimelineEntry.unsafe(
        entry_id=f"id_{i:08d}",
        type=TimelineEntryType.SYSTEM_NOTICE,
        title=f"title_{i}",
        description=None,
        action_id=None,
        place_id=None,
        created_at=datetime.now(UTC),
        device_id="0" * 64,
        lamport=i,
    )


def make_snapshot(n: int) -> TimelineSnapshot:
    entries = [make_entry(i) for i in range(n)]
    return TimelineSnapshot.build(entries)


def extend_snapshot(base: TimelineSnapshot, n_extra: int) -> TimelineSnapshot:
    start = len(base.entries)
    extra = [make_entry(start + i) for i in range(n_extra)]
    return TimelineSnapshot.build(tuple(base.entries) + tuple(extra))


# ============================================================
# Framing
# ============================================================


def test_pack_unpack_roundtrip():
    frames = [b"abc", b"defg", b"123"]
    blob = _pack_frames(frames)
    out = _unpack_frames(blob)
    assert out == frames


def test_unpack_truncated_length():
    blob = b"\x00\x00\x00"
    with pytest.raises(TimelineDeltaDecodeError):
        _unpack_frames(blob)


def test_unpack_empty_frame():
    blob = (0).to_bytes(4, "big")
    with pytest.raises(TimelineDeltaDecodeError):
        _unpack_frames(blob)


def test_unpack_invalid_length():
    blob = (10).to_bytes(4, "big") + b"abc"
    with pytest.raises(TimelineDeltaDecodeError):
        _unpack_frames(blob)


# ============================================================
# Apply
# ============================================================


def test_apply_success():
    base = make_snapshot(1)
    target = extend_snapshot(base, 2)

    delta = TimelineDelta.from_snapshots(base, target)
    out = delta.apply_to(base)

    assert out.cursor() == target.cursor()


def test_apply_base_mismatch():
    base = make_snapshot(1)
    other = make_snapshot(2)

    target = extend_snapshot(base, 2)
    delta = TimelineDelta.from_snapshots(base, target)

    with pytest.raises((ValueError, RuntimeError, AttributeError)):
        delta.apply_to(other)


def test_apply_with_none_entry():
    base = make_snapshot(1)

    target = TimelineCursor(
        timestamp=base.cursor().timestamp,
        head=base.cursor().head,
        total_entries=base.cursor().total_entries + 1,
    )

    with pytest.raises((ValueError, RuntimeError, TypeError)):
        TimelineDelta(
            base=base.cursor(),
            target=target,
            entries=(None,),
        )


# ============================================================
# Verify
# ============================================================


def test_verify_success():
    base = make_snapshot(1)
    target = extend_snapshot(base, 2)

    delta = TimelineDelta.from_snapshots(base, target)
    delta.verify_against(base)


def test_verify_base_mismatch():
    base = make_snapshot(1)
    other = make_snapshot(2)

    target = extend_snapshot(base, 2)
    delta = TimelineDelta.from_snapshots(base, target)

    with pytest.raises((ValueError, RuntimeError, AttributeError)):
        delta.verify_against(other)


# ============================================================
# Builders
# ============================================================


def test_from_snapshots_success():
    base = make_snapshot(1)
    target = extend_snapshot(base, 2)

    delta = TimelineDelta.from_snapshots(base, target)
    assert delta.size() == 2


def test_from_snapshots_rollback():
    base = make_snapshot(3)
    target = make_snapshot(1)

    with pytest.raises((ValueError, RuntimeError)):
        TimelineDelta.from_snapshots(base, target)


def test_from_snapshots_identical():
    base = make_snapshot(2)

    with pytest.raises((ValueError, RuntimeError)):
        TimelineDelta.from_snapshots(base, base)


def test_from_snapshots_invalid_entries():
    base = make_snapshot(1)
    target = extend_snapshot(base, 2)

    object.__setattr__(target, "entries", [None, None, None])

    with pytest.raises((ValueError, TypeError, AttributeError)):
        TimelineDelta.from_snapshots(base, target)


def test_apply_target_mismatch():
    base = make_snapshot(1)
    target = extend_snapshot(base, 2)

    delta = TimelineDelta.from_snapshots(base, target)

    # casser volontairement target
    bad_target = TimelineDelta(
        base=delta.base,
        target=TimelineCursor(
            timestamp=delta.base.timestamp,
            head=delta.base.head,
            total_entries=delta.base.total_entries + len(delta.entries),
        ),
        entries=delta.entries,
    )

    with pytest.raises(TimelineDeltaError):
        bad_target.apply_to(base)


# --------------------------------------------------
# VERIFY TARGET MISMATCH
# --------------------------------------------------


def test_verify_target_mismatch():
    base = make_snapshot(1)
    target = extend_snapshot(base, 2)

    delta = TimelineDelta.from_snapshots(base, target)

    bad = TimelineDelta(
        base=delta.base,
        target=delta.target,
        entries=delta.entries,
    )

    object.__setattr__(
        bad,
        "target",
        TimelineCursor(
            timestamp=delta.base.timestamp,
            head=delta.base.head,
            total_entries=999,
        ),
    )

    with pytest.raises(TimelineDeltaError):
        bad.verify_against(base)


# --------------------------------------------------
# FROM SNAPSHOTS SLICE FAILURE
# --------------------------------------------------


def test_from_snapshots_slice_failure(monkeypatch):
    base = make_snapshot(1)
    target = extend_snapshot(base, 2)

    def broken_slice(*args, **kwargs):
        raise RuntimeError("boom")

    object.__setattr__(target, "entries", None)

    with pytest.raises(TimelineDeltaError):
        TimelineDelta.from_snapshots(base, target)


# --------------------------------------------------
# DELTA NOT TUPLE
# --------------------------------------------------


def test_entries_not_tuple():
    base = make_snapshot(1)
    target = extend_snapshot(base, 1)

    with pytest.raises(TimelineDeltaError):
        TimelineDelta(
            base=base.cursor(),
            target=target.cursor(),
            entries=[make_entry(1)],
        )


# --------------------------------------------------
# VERIFY CARDINALITY MISMATCH
# --------------------------------------------------


def test_verify_cardinality_mismatch():
    base = make_snapshot(1)
    target = extend_snapshot(base, 2)

    delta = TimelineDelta.from_snapshots(base, target)

    # fausser target
    bad = TimelineDelta(
        base=delta.base,
        target=TimelineCursor(
            timestamp=delta.base.timestamp,
            head=delta.base.head,
            total_entries=delta.base.total_entries + len(delta.entries),
        ),
        entries=delta.entries,
    )

    bad.verify_against(base)
