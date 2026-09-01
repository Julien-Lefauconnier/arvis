# tests/timeline/test_timeline_commitment_contract.py
"""TimelineCommitment: verification, wire roundtrip, rejection rules.

Campaign RELEASE (LOT R2). The commitment is the audit anchor of a
timeline: it must equal itself across rebuilds, refuse a diverging
snapshot, survive a byte roundtrip, and reject malformed bytes
loudly (bad JSON, bad head shape, bad counters) rather than
constructing a half-valid anchor.
"""

from __future__ import annotations

import json

import pytest

from arvis.timeline.timeline_commitment import TimelineCommitment
from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_snapshot import TimelineSnapshot
from arvis.timeline.timeline_types import TimelineEntryType
from arvis.types.timestamps import utcnow


def _entry(seq: int) -> TimelineEntry:
    return TimelineEntry.unsafe(
        entry_id=f"audit-entry-{seq:04d}",
        type=TimelineEntryType.SYSTEM_NOTICE,
        title=f"entry {seq}",
        description=None,
        action_id=None,
        created_at=utcnow(),
    )


def _snapshot(n: int) -> TimelineSnapshot:
    return TimelineSnapshot.build(_entry(i) for i in range(n))


def test_commitment_is_stable_across_rebuilds_of_the_same_snapshot() -> None:
    snap = _snapshot(3)

    first = TimelineCommitment.from_snapshot(snap)
    second = TimelineCommitment.from_snapshot(snap)

    assert first == second
    first.verify_against(snap)


def test_commitment_refuses_a_diverging_snapshot() -> None:
    committed = TimelineCommitment.from_snapshot(_snapshot(2))

    with pytest.raises(ValueError, match="mismatch"):
        committed.verify_against(_snapshot(3))


def test_bytes_roundtrip_preserves_the_anchor() -> None:
    commitment = TimelineCommitment.from_snapshot(_snapshot(2))

    loaded = TimelineCommitment.from_bytes(commitment.to_bytes())

    assert loaded.head == commitment.head
    assert loaded.total_entries == commitment.total_entries
    assert loaded.timestamp_iso == commitment.timestamp_iso


def test_from_bytes_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="invalid commitment bytes"):
        TimelineCommitment.from_bytes(b"not json at all")


def test_from_bytes_rejects_a_malformed_head() -> None:
    base = json.loads(TimelineCommitment.from_snapshot(_snapshot(1)).to_bytes())

    short = dict(base, head="abc123")
    with pytest.raises(ValueError, match="invalid head length"):
        TimelineCommitment.from_bytes(json.dumps(short).encode())

    non_hex = dict(base, head="z" * 64)
    with pytest.raises(ValueError, match="invalid head format"):
        TimelineCommitment.from_bytes(json.dumps(non_hex).encode())


def test_from_bytes_rejects_bad_counters() -> None:
    base = json.loads(TimelineCommitment.from_snapshot(_snapshot(1)).to_bytes())

    not_int = dict(base, total_entries="3")
    with pytest.raises(ValueError, match="invalid total_entries"):
        TimelineCommitment.from_bytes(json.dumps(not_int).encode())

    negative = dict(base, total_entries=-1)
    with pytest.raises(ValueError, match="invalid total_entries"):
        TimelineCommitment.from_bytes(json.dumps(negative).encode())
