# tests/adversarial/test_timeline_adversarial.py


from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_types import TimelineEntryType


def make_entry(i: int):
    return TimelineEntry.unsafe(
        entry_id=str(i).zfill(8),
        type=TimelineEntryType.SYSTEM_NOTICE,
        title="t",
        description=None,
        action_id=None,
    )


def test_hashchain_tampering_detection():
    entries = [make_entry(i) for i in range(5)]


    entries[2] = make_entry(999)

    ids = [e.entry_id for e in entries]


    assert len(set(ids)) == len(ids)


def test_duplicate_entry_attack():
    e = make_entry(1)
    entries = [e, e, e]

    ids = [x.entry_id for x in entries]


    assert len(set(ids)) < len(ids)

def test_entry_id_collision_attack():
    e1 = make_entry(1)
    e2 = make_entry(1)

    assert e1.entry_id == e2.entry_id