# tests/timeline/helpers.py

from datetime import datetime, timezone

from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_types import TimelineEntryType


def make_entry(i: int) -> TimelineEntry:
    return TimelineEntry.unsafe(
        entry_id=f"entry{i:04d}",
        created_at=datetime.now(timezone.utc),
        type=TimelineEntryType.SYSTEM_NOTICE,
        title=f"title{i}",
        description=f"description{i}",
        action_id=None,
        place_id=None,
        origin_ref=None,
    )


def make_entries(n: int):
    return [make_entry(i) for i in range(n)]
