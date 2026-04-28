# tests/timeline/test_hashchain_edge_cases.py

from datetime import UTC, datetime

import pytest

from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_hashchain import TimelineHashChain
from arvis.timeline.timeline_types import TimelineEntryType


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


def test_invalid_hash_length():
    with pytest.raises(ValueError):
        TimelineHashChain(("abc",))


def test_invalid_hash_characters():
    with pytest.raises(ValueError):
        TimelineHashChain(("z" * 64,))


def test_verify_failure():
    e = make_entry(0)
    chain = TimelineHashChain.build([e])

    with pytest.raises(ValueError):
        chain.verify([])
